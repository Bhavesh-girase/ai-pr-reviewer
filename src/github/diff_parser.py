import re

def parse_changed_file(file_data: dict) -> dict:
    """
    Parse the GitHub PR patch into a structured format.

    Parameters
    ----------
    file_data : dict
        One file object returned by the GitHub Pull Request Files API.

    Returns
    -------
    dict
        Structured information about the changed file.
    """

    patch = file_data.get("patch", "")

    file_change = {
        "filename": file_data["filename"],
        "status": file_data["status"],
        "additions": file_data["additions"],
        "deletions": file_data["deletions"],
        "changes": file_data["changes"],
        "added_lines": [],
        "removed_lines": [],
        "patch": patch,
    }

    current_old_line = 0
    current_new_line = 0

    for line in patch.splitlines():

        # Parse hunk headers
        if line.startswith("@@"):
            match = re.match(r"^@@\s+-(\d+),?\d*\s+\+(\d+),?\d*\s+@@", line)
            if match:
                current_old_line = int(match.group(1))
                current_new_line = int(match.group(2))
            continue

        # Skip other diff metadata
        if line.startswith("\\"):
            continue

        # Added line
        if line.startswith("+") and not line.startswith("+++"):
            file_change["added_lines"].append({
                "line": current_new_line,
                "text": line[1:].rstrip()
            })
            current_new_line += 1

        # Removed line
        elif line.startswith("-") and not line.startswith("---"):
            file_change["removed_lines"].append({
                "line": current_old_line,
                "text": line[1:].rstrip()
            })
            current_old_line += 1
            
        else:
            # Unchanged context line
            current_old_line += 1
            current_new_line += 1

    return file_change