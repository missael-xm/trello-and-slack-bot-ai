# src/templates/new_design_chain_template.py
NEW_DESIGN_CHAIN_TEMPLATE = """
Follow the indications and instructions to make decisions.

Information related to web design has these characteristics:
  - Visual and aesthetic: Look for topics such as user interface design (UI),
    user experience (UX), color design, and typography.
  - Design principles: Look at concepts such as visual hierarchy, consistency,
    accessibility, and usability.
  - Structure and arrangement of elements: consider the organization of
    content, navigation design and information architecture.
  - User experience evaluation: Find information on usability testing, user
    research, and data analysis.

Information related to web development has these characteristics:
  - Design References for Development: Screenshots and/or figma links.
  - Requests: Graphic design request message for web development.
  - References to backend technologies: Node.js, Express, Django, Flask, etc.
  - Descriptions of web-related programming languages: Python, JavaScript, etc.
  - Database and data storage conversations: MySQL, PostgreSQL, MongoDB, etc.
  - Mentions of web security concepts: HTTPS, authentication and authorization,
    etc.
  - Topics related to web design: UX/UI, responsive design, accessibility, etc.

Instructions to generate the request message:
  - Analyze the information well and synthesize it in an understandable way.
  - Do not assume information that is not explicitly requested.
  - Only use information related to web development.
  - Do not add information.
  - Always include the links that have this format "[value1](value2)".
  - The message must be as faithful as possible to the information provided.

This description is related to web design or web development? (design/dev)
<<{card_description}>>

When is "design":
  - Do nothing and the final answer is empty.

When is "dev":
  - Generates a request message in third person.

###

Output format:
{format_instructions}
"""