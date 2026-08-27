def build_search_query(file_change: dict)->str:
    """ Build a retrieval query for a one changed file """

    filename=file_change.get(
        "filename",
        ""
    )

    added_lines=[l["text"] for l in file_change.get("added_lines", [])]
    removed_lines=[l["text"] for l in file_change.get("removed_lines", [])]

    query="\n".join(

        [
            filename,
            *added_lines,
            *removed_lines,
        ]
    )
    return query
    
    