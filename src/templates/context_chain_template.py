# src/templates/context_chain_template.py
CONTEXT_CHAIN_TEMPLATE = """
Be guided by the format of the comments, follow the indications and
instructions to make decisions.

Comment format:
  [author: username - comment date: YYYY-MM-DDTHH:MM:SS.mmmZ]comment

Indications to understand the format of a comment:
  - "author" indicates who made the comment.
  - "comment date" indicates the date the comment was made.
  - Mentions have this format "@username".
  - Mentions are used to know when the person who made the comment is
    addressing someone.

Instructions for extracting comments:
  - Extract comments from the comment history that are related to the recent
    comment and are in the same context and conversation topic.
  - Although the comment history is empty it always add the recent comment as
    the last extracted comment.
  - Do not modify the extracted comments in any way, EXCEPT for cleaning invalid characters (see below).
  - Sort from oldest to newest date.

### CRITICAL JSON FORMATTING RULES:
1. **NO HEX ESCAPES:** You must NOT use hex escapes like `\\x0a` or `\\xa0`. This breaks the JSON.
2. **CLEAN TEXT:** Replace any non-breaking space (\\xa0) with a normal space.
3. **ESCAPE BACKSLASHES:** If the text contains a backslash (e.g. file paths), escape it as `\\\\`.
4. **UNICODE:** If you need to represent special characters, use the literal character or `\\uXXXX` format.
5. **STRICT JSON:** The output must be parsable by `json.loads()`.

Recent comment: {recent_comment}
Comment history: {card_comment_history}

Is the "author" of the recent comment one of these {allowed_users}
users? (yes/no)

When is "yes":
  Is the recent comment a question? (question/other/confirmation)

When is "no":
  Is the recent comment a request? (request/feedback/confirmation)

When is "question" or "other":
  Do nothing and the final answer is empty.

When is "request" or "confirmation" or "feedback":
  Extract comments and clean them.

###

Output format:
{format_instructions}
"""