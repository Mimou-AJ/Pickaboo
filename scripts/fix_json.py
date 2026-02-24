
lines = open('data/products_small.json').readlines()
# Find the last line with "}," (end of an object)
last_obj_end = -1
for i in range(len(lines) - 1, -1, -1):
    if lines[i].strip() == "}," or lines[i].strip() == "}":
        last_obj_end = i
        break

if last_obj_end != -1:
    # Keep up to that line
    lines = lines[:last_obj_end+1]
    # Remove comma if present (lines usually have indentation)
    if ',' in lines[-1]:
        lines[-1] = lines[-1].rsplit(',', 1)[0] + "\n"
        
    # Add closing bracket
    lines.append("]\n")
    
    with open('data/products_small.json', 'w') as f:
        f.writelines(lines)
    print("Fixed JSON")
else:
    print("Could not find object boundary")
