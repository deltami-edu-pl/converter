#!/usr/bin/env python3

from bs4 import BeautifulSoup
import re

def clean_html(html_content):
    # Remove unnecessary whitespace and newlines
    html_content = re.sub(r'\s+', ' ', html_content)
    html_content = html_content.strip()
    return html_content

def process_exercises(input_file):
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
        # Clean the content
        hint_content = clean_html(str(hint))
        problem_content = clean_html(str(problem))
        
        # Create exercise element
        exercise = f"""<!-- EXERCISE BEGIN -->
<div class="exercise">
  {problem_content}
  <header class="answer">
    <a href="javascript:void(0)">Wskazówka</a>
  </header>
  <div class="answer-content">
    {hint_content}
  </div>
</div>
<!-- EXERCISE END   -->"""
        
        exercises.append(exercise)
    
    # Write the output
    output_file = input_file.replace('.html', '-exercises.html')
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write('\n\n'.join(exercises))
    
    print(f"Created {output_file} with {len(exercises)} exercises")

if __name__ == "__main__":
    import sys
    if len(sys.argv) != 2:
        print("Usage: python process_exercises.py <input_html_file>")
        sys.exit(1)
    
    process_exercises(sys.argv[1]) 