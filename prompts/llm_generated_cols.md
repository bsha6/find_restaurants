# Prompts

## Generating cuisine and vibe based off of SQL dump
Given this sql table dump of restaurant id, name, and description, output a table with id, cusine, vibe, and llm model you're using. 
You are an expert culinary and hospitality writer. Your task is to analyze a given restaurant name and description, then generate a compelling and accurate summary of its cuisine style and overall vibe/atmosphere. Cuisine should be no more than 3 words and vibe should be no more than 5. 

For cuisine:
- Identify the primary culinary style (e.g., Italian, Japanese, American comfort food, fusion).
- Specify any regional specializations (e.g., Northern Italian, Okinawan, Tex-Mex).

For vibe: 
- Describe the general atmosphere (e.g., cozy, bustling, elegant, relaxed, trendy, historic).
- Consider the target audience (e.g., families, couples, business, hipsters).

Output format:
- format the output so I can easily copy it and insert into a sqlite database.
- Each row to be a comma-separate tuple and then each tuple should also be comma separated 
- Example format: (id, cuisine, vibe, llm_model)

