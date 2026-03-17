import os
import re
import markdown


def process_tables_in_file(filepath, fix_tables=False):
    """
    Processes markdown tables in a file.
    If fix_tables is True, ensures each table has a blank line before it.
    """
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()

        md = markdown.Markdown(extensions=["fenced_code"])
        html_content = md.convert(content)

        code_blocks = list(
            re.finditer(r"<pre><code.*?>.*?</code></pre>", html_content, re.DOTALL)
        )

        code_block_data = []
        for match in code_blocks:
            code_block_data.append(
                {"start": match.start(), "end": match.end(), "content": match.group(0)}
            )

        def process_tables(text):
            temp_text = text
            for cb in code_block_data:
                temp_text = temp_text.replace(cb["content"], "CODE_BLOCK_PLACEHOLDER")

            pattern = r"(^#{2,3}\s+.*?\n)(\|.*?\|\n(?:\|.*\|\n)*)"

            def replacer(match):
                heading = match.group(1)
                table = match.group(2)
                if heading.endswith("\n\n"):
                    return match.group(0)
                if fix_tables:
                    return heading.rstrip() + "\n\n" + table
                return match.group(0)

            temp_text = re.sub(pattern, replacer, temp_text, flags=re.MULTILINE)

            for cb in code_block_data:
                temp_text = temp_text.replace("CODE_BLOCK_PLACEHOLDER", cb["content"])
            return temp_text

        updated_content = process_tables(content)

        with open(filepath, "w", encoding="utf-8") as f:
            f.write(updated_content)

        print(f"Processed {filepath}")
        if fix_tables:
            print("- Added blank lines before tables")
        return True

    except Exception as e:
        print(f"Error processing {filepath}: {e}")
        return False


def process_tables_in_markdown(directory, max_files=None, fix_tables=False):
    files_processed = 0
    for root, _, files in os.walk(directory):
        for filename in files:
            if filename.endswith(".md"):
                filepath = os.path.join(root, filename)
                success = process_tables_in_file(filepath, fix_tables)
                if success:
                    files_processed += 1

                if max_files and files_processed >= max_files:
                    print(f"Maximum files processed ({max_files}). Exiting directory.")
                    return
