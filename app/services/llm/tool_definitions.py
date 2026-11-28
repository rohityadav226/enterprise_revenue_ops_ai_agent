GET_PIPELINE_OVERVIEW_TOOL = {
    "type": "function",
    "name": "get_pipeline_overview",
    "description": (
        "Retrieve the open sales pipeline overview. "
        "Use this when the user asks about open pipeline, "
        "weighted pipeline, average opportunity value, "
        "weighted probability, or pipeline totals. "
        "Optionally filter by sales region. "
        "Do not use this function for actual bookings."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "region": {
                "type": ["string", "null"],
                "description": (
                    "Sales region to filter by, such as North or South. "
                    "Use null when no region is specified."
                )
            }
        },
        "required": ["region"],
        "additionalProperties": False
    },
    "strict": True
}


REVOPS_TOOLS = [
    GET_PIPELINE_OVERVIEW_TOOL
]