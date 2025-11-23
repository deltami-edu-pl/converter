#!/usr/bin/env python3

from bs4 import BeautifulSoup
import re

def clean_html(html_content):
    # Remove unnecessary whitespace and newlines
    html_content = re.sub(r'\s+', ' ', html_content)
    html_content = html_content.strip()
    return html_content

def get_content_without_li(li_element):
    # Get the content without the li tags
    content = ''
    for child in li_element.children:
        if child.name is not None:  # Skip text nodes
            content += str(child)
    return clean_html(content)

def convert_zadania(input_file):
    # Read the HTML file
    with open(input_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Parse HTML
    soup = BeautifulSoup(content, 'html.parser')
    
    # Find all ordered lists
    lists = soup.find_all('ol')
    
    if len(lists) < 2:
        print("Error: Need at least two ordered lists in the input file")
        return
    
    # Get hints and problems lists
    hints_list = lists[0]
    problems_list = lists[1]
    
    # Create new content with exercises
    exercises = []
    
    # Process each pair of items
    for hint, problem in zip(hints_list.find_all('li'), problems_list.find_all('li')):
        # Get the content without the li tags
        problem_content = get_content_without_li(problem)
        hint_content = get_content_without_li(hint)
        
        # Create exercise element
        exercise = f"""<!-- EXERCISE BEGIN -->
<li>
    <div class="exercise">
        {problem_content}
        <header class="answer">
            <a href="javascript:void(0)">Wskazówka</a>
        </header>
        <div class="answer-content">
            {hint_content}
        </div>
    </div>
</li>
<!-- EXERCISE END -->"""
        
        exercises.append(exercise)
    
    # Remove the first list (hints)
    lists[0].decompose()
    
    # Create new ol tag with exercises
    new_ol = soup.new_tag('ol')
    new_ol.append(BeautifulSoup('\n\n'.join(exercises), 'html.parser'))
    
    # Replace the second list with new ol containing exercises
    lists[1].replace_with(new_ol)
    
    # Write the output
    output_file = input_file.replace('.html', '-exercises.html')
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(str(soup))
    
    print(f"Created {output_file} with {len(exercises)} exercises")

if __name__ == "__main__":
    import sys
    if len(sys.argv) != 2:
        print("Usage: python convert_zadania.py <input_html_file>")
        sys.exit(1)
    
    convert_zadania(sys.argv[1]) 