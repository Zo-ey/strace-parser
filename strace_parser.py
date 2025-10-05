import re
import ast
#
# For more insightful outputs, use with the `--decode-fds=path,socket,pidfd` option of strace.
def parse_strace_line(line):
    # Split syscall from return value
    if "=" in line:
        syscall_part, ret_part = line.split(" = ", 1)
        ret_part = ret_part.strip()
    else:
        syscall_part, ret_part = line, None

    # Extract syscall name and args
    match = re.match(r"([^\(]*)\((.*)\)", syscall_part.strip())
    if not match:
        return None
    
    name, raw_args = match.groups()
    args = split_args(raw_args)

    return {
        "name": name,
        "args": args,
        "ret": parse_return(ret_part)
    }

def split_args(raw_args):
    # Split by commas. TODO: refine later for arrays/strings
    parts = [arg.strip() for arg in re.split(r", (?=(?:[^\"]*\"[^\"]*\")*[^\"]*$)", raw_args)]
    parsed = []
    for i, p in enumerate(parts):
        if p.startswith('"') and p.endswith('"'):
            parsed.append({"index": i, "type": "string", "value": p.strip('"')})
        elif p.startswith("[") and p.endswith("]"):
            parsed.append({"index": i, "type": "array", "value": ast.literal_eval(p)})
        elif "|" in p:
            parsed.append({"index": i, "type": "flags", "value": p.split("|")})
        elif p.startswith("0x"):
            parsed.append({"index": i, "type": "pointer", "value": p})
        elif p.isdigit() or (p.startswith("-") and p[1:].isdigit()):
            parsed.append({"index": i, "type": "int", "value": int(p)})
        else:
            parsed.append({"index": i, "type": "constant", "value": p})
    return parsed

def parse_return(ret_part):
    if not ret_part:
        return None
    if " " in ret_part and ret_part.strip().startswith("-1"):
        # error case
        parts = ret_part.split(" ", 2)
        return {"value": int(parts[0]), "error": parts[1], "description": parts[2].strip("() ")}
    if ret_part.isdigit():
        return {"value": int(ret_part)}
    return {"value": ret_part}
