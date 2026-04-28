"""List all subjects and identify which to keep/delete."""
import boto3

ddb = boto3.resource("dynamodb")
table = ddb.Table("academic-pipeline-subjects-dev")

resp = table.scan(FilterExpression="SK = :sk", ExpressionAttributeValues={":sk": "STATE"})
items = resp.get("Items", [])

# Sort by updated_at descending
items.sort(key=lambda x: x.get("updated_at", ""), reverse=True)

print(f"Total records: {len(items)}\n")
print(f"{'#':>3} {'State':<22} {'Updated':<28} {'Name':<50} {'ID'}")
print("-" * 140)

for i, item in enumerate(items):
    marker = "KEEP" if i < 3 else "DELETE"
    print(f"{i+1:>3} {item.get('current_state',''):<22} {item.get('updated_at','')[:25]:<28} {item.get('subject_name','')[:50]:<50} {item['subject_id']} [{marker}]")

# Delete all except the 3 most recent
keep_ids = {items[i]["subject_id"] for i in range(min(3, len(items)))}
delete_ids = [item["subject_id"] for item in items if item["subject_id"] not in keep_ids]

print(f"\nKeeping {len(keep_ids)}: {keep_ids}")
print(f"Deleting {len(delete_ids)}")

if delete_ids:
    confirm = input("\nType 'yes' to delete: ")
    if confirm == "yes":
        for sid in delete_ids:
            table.delete_item(Key={"subject_id": sid, "SK": "STATE"})
            print(f"  Deleted: {sid}")
        print("Done")
    else:
        print("Cancelled")
