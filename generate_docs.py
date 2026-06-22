import json

with open("openapi.json", "r") as f:
    spec = json.load(f)

markdown = ["# 📖 Zinesave Backend API Contracts\n"]
markdown.append(
    "Esta documentación genera automáticamente todos los endpoints, sus requerimientos (Body/Query) y las estructuras de sus respuestas (Response Models) basados en el esquema OpenAPI de FastAPI.\n"
)

paths = spec.get("paths", {})
components = spec.get("components", {}).get("schemas", {})


def get_ref_name(ref):
    if not ref:
        return ""
    return ref.split("/")[-1]


def parse_schema(schema_obj, level=0):
    if not schema_obj:
        return "Any"

    if "$ref" in schema_obj:
        ref_name = get_ref_name(schema_obj["$ref"])
        return f"**{ref_name}**"

    if schema_obj.get("type") == "array":
        items = parse_schema(schema_obj.get("items", {}))
        return f"Array<{items}>"

    if schema_obj.get("type") == "object":
        props = schema_obj.get("properties", {})
        if not props:
            return "Object"
        out = "{\n"
        indent = "  " * (level + 1)
        for k, v in props.items():
            type_str = parse_schema(v, level + 1)
            req = k in schema_obj.get("required", [])
            opt_mark = "" if req else "?"
            out += f"{indent}{k}{opt_mark}: {type_str},\n"
        out += ("  " * level) + "}"
        return out

    if "anyOf" in schema_obj:
        types = [parse_schema(t, level) for t in schema_obj["anyOf"]]
        return " | ".join(types)

    return schema_obj.get("type", "Any")


for path, methods in paths.items():
    for method, details in methods.items():
        markdown.append(f"## `{method.upper()}` {path}")
        if "summary" in details:
            markdown.append(f"> {details['summary']}\n")

        # Parameters (Query, Path)
        if "parameters" in details:
            markdown.append("### 📥 Parameters")
            for param in details["parameters"]:
                req = "*(Required)*" if param.get("required") else "*(Optional)*"
                schema_type = param.get("schema", {}).get("type", "string")
                markdown.append(f"- `{param['name']}` ({param['in']}): {schema_type} {req}")
            markdown.append("")

        # Request Body
        if "requestBody" in details:
            content = details["requestBody"].get("content", {})
            if "application/json" in content:
                schema = content["application/json"].get("schema", {})
                markdown.append("### 📤 Request Body (JSON)")
                if "$ref" in schema:
                    ref_name = get_ref_name(schema["$ref"])
                    markdown.append(f"Model: **{ref_name}**")
                    resolved_schema = components.get(ref_name, {})
                    markdown.append("```typescript\n" + parse_schema(resolved_schema) + "\n```")
                else:
                    markdown.append("```typescript\n" + parse_schema(schema) + "\n```")
            markdown.append("")

        # Responses
        if "responses" in details:
            markdown.append("### 📦 Responses")
            for status_code, response in details["responses"].items():
                desc = response.get("description", "")
                content = response.get("content", {})

                markdown.append(f"**Status {status_code}**: {desc}")

                if "application/json" in content:
                    schema = content["application/json"].get("schema", {})
                    if "$ref" in schema:
                        ref_name = get_ref_name(schema["$ref"])
                        resolved_schema = components.get(ref_name, {})
                        markdown.append(f"*Model: {ref_name}*")
                        markdown.append("```typescript\n" + parse_schema(resolved_schema) + "\n```")
                    elif schema.get("type") == "array" and "$ref" in schema.get("items", {}):
                        ref_name = get_ref_name(schema["items"]["$ref"])
                        resolved_schema = components.get(ref_name, {})
                        markdown.append(f"*Model: Array<{ref_name}>*")
                        markdown.append(
                            "```typescript\nArray<\n" + parse_schema(resolved_schema) + "\n>\n```"
                        )
                    else:
                        markdown.append("```typescript\n" + parse_schema(schema) + "\n```")
            markdown.append("\n---")


markdown.append("\n## 🧩 Common Models (Component Schemas)\n")
for name, schema in components.items():
    if name == "HTTPValidationError" or name == "ValidationError":
        continue
    markdown.append(f"### {name}")
    markdown.append("```typescript\n" + parse_schema(schema) + "\n```\n")

with open(
    "/Users/dahch/.gemini/antigravity-ide/brain/ec013902-8357-4e13-9457-35bafe76af4e/api_contracts.md",
    "w",
) as f:
    f.write("\n".join(markdown))
