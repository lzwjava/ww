import os
import re
import markdown


def fix_mathjax_in_file(filepath, gemini=False, reset=False):
    r"""
    Replaces instances of \( and \) with \\( and \\) respectively in a markdown file,
    skipping code blocks. If gemini is True, also replaces $ $ with \\( and \\).
    If reset is True, performs the reverse operation: \\( to \(, \\) to \), etc.
    """
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()

        if not reset and (
            re.search(r"\\\\\(", content) or re.search(r"\\\\\[", content)
        ):
            print(f"Skipping {filepath}: Already contains \\( or \\[")
            return False

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

        def replace_mathjax(text, gemini=False, reset=False):
            temp_text = text
            for cb in code_block_data:
                temp_text = temp_text.replace(cb["content"], "CODE_BLOCK_PLACEHOLDER")

            if reset:
                temp_text = re.sub(r"\\\\\(", r"\(", temp_text)
                temp_text = re.sub(r"\\\\\)", r"\)", temp_text)
                temp_text = re.sub(r"\\\\\[", r"\[", temp_text)
                temp_text = re.sub(r"\\\\\]", r"\]", temp_text)
                if gemini:
                    temp_text = re.sub(r"\\\\\((.*?)\\\\\)", r"$\1$", temp_text)
            else:
                temp_text = re.sub(r"\\\(", r"\\\\(", temp_text)
                temp_text = re.sub(r"\\\)", r"\\\\)", temp_text)
                temp_text = re.sub(r"\\\[", r"\\\\[", temp_text)
                temp_text = re.sub(r"\\\]", r"\\\\]", temp_text)
                if gemini:
                    temp_text = re.sub(r"\$(.*?)\$", r"\\\\(\1\\\\)", temp_text)

            for cb in code_block_data:
                temp_text = temp_text.replace("CODE_BLOCK_PLACEHOLDER", cb["content"])
            return temp_text

        updated_content = replace_mathjax(content, gemini, reset)
        replacements_made = content != updated_content

        if replacements_made:
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(updated_content)
            action = "Reversed" if reset else "Fixed"
            print(f"{action} MathJax delimiters in {filepath}: Replacements made")
        else:
            print(f"Processed {filepath}: No replacements needed")

        return replacements_made

    except Exception as e:
        print(f"Error processing {filepath}: {e}")
        return False


def fix_mathjax_in_markdown(directory, max_files=None, gemini=False, reset=False):
    files_processed = 0
    for root, _, files in os.walk(directory):
        for filename in files:
            if filename.endswith(".md"):
                filepath = os.path.join(root, filename)
                success = fix_mathjax_in_file(filepath, gemini, reset)
                if success:
                    files_processed += 1

                if max_files and files_processed >= max_files:
                    print(f"Maximum files processed ({max_files}). Exiting directory.")
                    return
