#!/usr/bin/env python3
"""
Markdown to Jenzabar LMS Cartridge Converter
Converts exam markdown files to Jenzabar/Blackboard compatible import format.
"""

import re
import uuid
import zipfile
import html
import sys
import os

def parse_markdown_exam(md_content):
    """Parse markdown exam content into structured question data."""
    questions = []
    
    # Split into lines for processing
    lines = md_content.split('\n')
    
    current_question = None
    current_choices = []
    in_choices = False
    question_num = 0
    
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        
        # Detect question start (bold number pattern)
        q_match = re.match(r'\*\*(\d+)\.\s*(.+?)(?:\*\*)?$', line)
        if q_match:
            # Save previous question if exists
            if current_question and current_choices:
                questions.append({
                    'num': question_num,
                    'text': current_question,
                    'choices': current_choices,
                    'answer': None,
                    'rationale': None,
                    'type': 'mc'
                })
            
            question_num = int(q_match.group(1))
            question_text = q_match.group(2).rstrip('*')
            
            # Check if question continues on next lines (before choices)
            i += 1
            while i < len(lines):
                next_line = lines[i].strip()
                # Stop if we hit a choice, answer, or new question
                if re.match(r'^[A-E]\.\s+', next_line) or next_line.startswith('**Answer:') or re.match(r'\*\*\d+\.', next_line):
                    break
                if next_line and not next_line.startswith('#'):
                    question_text += ' ' + next_line
                i += 1
            
            current_question = question_text.strip()
            current_choices = []
            in_choices = True
            continue
        
        # Detect choices (A. B. C. D. E.)
        choice_match = re.match(r'^([A-E])\.\s+(.+)$', line)
        if choice_match and in_choices:
            choice_letter = choice_match.group(1)
            choice_text = choice_match.group(2)
            current_choices.append({
                'letter': choice_letter,
                'text': choice_text
            })
            i += 1
            continue
        
        # Detect answer
        answer_match = re.match(r'\*\*Answer:\s*([A-E,\s]+|TRUE|FALSE)\*\*', line, re.IGNORECASE)
        if answer_match:
            answer = answer_match.group(1).strip().upper()
            
            # Check if this is a True/False question
            if answer in ['TRUE', 'FALSE']:
                # This is a T/F question - create choices if not present
                if not current_choices:
                    current_choices = [
                        {'letter': 'A', 'text': 'True'},
                        {'letter': 'B', 'text': 'False'}
                    ]
                # Map TRUE/FALSE to A/B
                answer = 'A' if answer == 'TRUE' else 'B'
                q_type = 'tf'
            else:
                # Check if multiple answers (comma-separated like "A, B, C")
                if ',' in answer:
                    q_type = 'ma'
                else:
                    q_type = 'mc'

            # Look for rationale on next lines
            rationale = ''
            i += 1
            while i < len(lines):
                next_line = lines[i].strip()
                if next_line.startswith('**Rationale:'):
                    rationale = next_line.replace('**Rationale:**', '').strip()
                    i += 1
                    # Continue reading rationale if it spans multiple lines
                    while i < len(lines) and lines[i].strip() and not lines[i].strip().startswith('---') and not re.match(r'\*\*\d+\.', lines[i].strip()):
                        rationale += ' ' + lines[i].strip()
                        i += 1
                    break
                elif next_line.startswith('---') or re.match(r'\*\*\d+\.', next_line) or next_line.startswith('##'):
                    break
                i += 1
            
            # Save the question
            if current_question:
                questions.append({
                    'num': question_num,
                    'text': current_question,
                    'choices': current_choices,
                    'answer': answer.replace(' ', '').split(','),  # Handle multiple answers like "A, B, C"
                    'rationale': rationale.strip(),
                    'type': q_type
                })
            
            current_question = None
            current_choices = []
            in_choices = False
            continue
        
        i += 1
    
    return questions

def escape_xml(text):
    """Escape text for XML/HTML."""
    return html.escape(str(text))

def generate_questions_dat(questions, title):
    """Generate the questions.dat XML file content."""
    
    xml_parts = ['''<?xml version="1.0" encoding="UTF-8"?>
<questestinterop>
  <assessment title="{}">
    <assessmentmetadata>
      <bbmd_asi_object_id>assessment_1</bbmd_asi_object_id>
      <bbmd_asitype>Assessment</bbmd_asitype>
      <bbmd_assessmenttype>Pool</bbmd_assessmenttype>
      <bbmd_sectiontype>Subsection</bbmd_sectiontype>
      <bbmd_questiontype>Multiple Choice</bbmd_questiontype>
      <bbmd_is_from_cartridge>false</bbmd_is_from_cartridge>
      <bbmd_numbertype>none</bbmd_numbertype>
      <bbmd_partialcredit />
      <bbmd_orientationtype>vertical</bbmd_orientationtype>
      <bbmd_is_extracredit>false</bbmd_is_extracredit>
      <qmd_absolutescore_max>{}</qmd_absolutescore_max>
      <qmd_weighting>0.0</qmd_weighting>
    </assessmentmetadata>
    <rubric view="All">
      <flow_mat class="Block">
        <material>
          <mat_extension>
            <mat_formattedtext type="HTML" />
          </mat_extension>
        </material>
      </flow_mat>
    </rubric>
    <presentation_material>
      <flow_mat class="Block">
        <material>
          <mat_extension>
            <mat_formattedtext type="HTML">{}</mat_formattedtext>
          </mat_extension>
        </material>
      </flow_mat>
    </presentation_material>
    <section>
      <sectionmetadata>
        <bbmd_asi_object_id>section_0</bbmd_asi_object_id>
        <bbmd_asitype>Section</bbmd_asitype>
        <bbmd_assessmenttype>Pool</bbmd_assessmenttype>
        <bbmd_sectiontype>Subsection</bbmd_sectiontype>
        <bbmd_questiontype>Multiple Choice</bbmd_questiontype>
        <bbmd_is_from_cartridge>false</bbmd_is_from_cartridge>
        <bbmd_numbertype>none</bbmd_numbertype>
        <bbmd_partialcredit />
        <bbmd_orientationtype>vertical</bbmd_orientationtype>
        <bbmd_is_extracredit>false</bbmd_is_extracredit>
        <qmd_absolutescore_max>{}</qmd_absolutescore_max>
        <qmd_weighting>0.0</qmd_weighting>
      </sectionmetadata>'''.format(escape_xml(title), len(questions), escape_xml(title), len(questions))]
    
    for idx, q in enumerate(questions):
        item_id = str(uuid.uuid4())
        if q['type'] == 'tf':
            q_type = 'True/False'
        elif q['type'] == 'ma':
            q_type = 'Multiple Answer'
        else:
            q_type = 'Multiple Choice'
        is_multi = len(q['answer']) > 1
        cardinality = 'Multiple' if is_multi else 'Single'
        
        # Build choices XML
        choices_xml = []
        for cidx, choice in enumerate(q['choices']):
            choice_id = f"I{idx}_C{cidx}"
            choice_xml = '''
                  <flow_label class="Block">
                    <response_label ident="{}" rshuffle="Yes" rarea="Ellipse" rrange="Exact">
                      <flow_mat class="FORMATTED_TEXT_BLOCK">
                        <material>
                          <mat_extension>
                            <mat_formattedtext type="HTML">&lt;div style="font-family:'times new roman';font-size:11pt;color:#000000;font-weight:normal;"&gt;{}&lt;/div&gt;</mat_formattedtext>
                          </mat_extension>
                        </material>
                      </flow_mat>
                    </response_label>
                  </flow_label>'''.format(choice_id, escape_xml(choice['text']))
            choices_xml.append(choice_xml)
        
        # Build correct answer response processing
        correct_indices = []
        for ans in q['answer']:
            for cidx, choice in enumerate(q['choices']):
                if choice['letter'] == ans:
                    correct_indices.append(cidx)
                    break
        
        # Feedback for correct answer
        feedback_text = q['rationale'] if q['rationale'] else 'Correct!'
        
        # Build respconditions
        respconditions = []
        
        # Correct answer condition
        if is_multi:
            # For multiple answers, need AND condition
            and_parts = ' '.join([f'<varequal respident="RESPONSE_I{idx}_R0" case="No">I{idx}_C{ci}</varequal>' for ci in correct_indices])
            correct_condition = f'''
        <respcondition title="correct">
          <conditionvar>
            <and>
              {and_parts}
            </and>
          </conditionvar>
          <setvar variablename="SCORE" action="Set">SCORE.max</setvar>
          <displayfeedback linkrefid="correct" feedbacktype="Response" />
        </respcondition>'''
        else:
            ci = correct_indices[0] if correct_indices else 0
            correct_condition = f'''
        <respcondition title="correct">
          <conditionvar>
            <varequal respident="RESPONSE_I{idx}_R0" case="No">I{idx}_C{ci}</varequal>
          </conditionvar>
          <setvar variablename="SCORE" action="Set">SCORE.max</setvar>
          <displayfeedback linkrefid="correct" feedbacktype="Response" />
        </respcondition>'''
        
        respconditions.append(correct_condition)
        
        # Incorrect condition
        incorrect_condition = '''
        <respcondition title="incorrect">
          <conditionvar>
            <other />
          </conditionvar>
          <setvar variablename="SCORE" action="Set">0</setvar>
          <displayfeedback linkrefid="incorrect" feedbacktype="Response" />
        </respcondition>'''
        respconditions.append(incorrect_condition)
        
        item_xml = f'''
      <item maxattempts="0">
        <itemmetadata>
          <bbmd_asi_object_id>{item_id}</bbmd_asi_object_id>
          <bbmd_asitype>Item</bbmd_asitype>
          <bbmd_keywords />
          <bbmd_assessmenttype>Pool</bbmd_assessmenttype>
          <bbmd_sectiontype>Subsection</bbmd_sectiontype>
          <bbmd_is_from_cartridge>false</bbmd_is_from_cartridge>
          <bbmd_numbertype>letter_lower</bbmd_numbertype>
          <bbmd_partialcredit>false</bbmd_partialcredit>
          <bbmd_orientationtype>vertical</bbmd_orientationtype>
          <bbmd_is_extracredit>false</bbmd_is_extracredit>
          <qmd_absolutescore_max>1</qmd_absolutescore_max>
          <qmd_weighting>0.0</qmd_weighting>
          <bbmd_questiontype>{q_type}</bbmd_questiontype>
        </itemmetadata>
        <presentation>
          <flow class="Block">
            <flow class="QUESTION_BLOCK">
              <flow class="FORMATTED_TEXT_BLOCK">
                <material>
                  <mat_extension>
                    <mat_formattedtext type="HTML">&lt;div style="font-family: 'times new roman'; font-size: 11pt; color: #000000; font-weight: normal;"&gt;{escape_xml(q['text'])}&lt;/div&gt;</mat_formattedtext>
                  </mat_extension>
                </material>
              </flow>
            </flow>
            <flow class="RESPONSE_BLOCK">
              <response_lid ident="RESPONSE_I{idx}_R0" rcardinality="{cardinality}" rtiming="No">
                <render_choice shuffle="Yes" minnumber="0" maxnumber="0">{''.join(choices_xml)}
                </render_choice>
              </response_lid>
            </flow>
          </flow>
        </presentation>
        <resprocessing scoremodel="SumOfScores">
          <outcomes>
            <decvar varname="SCORE" vartype="Decimal" defaultval="0" minvalue="0" maxvalue="1.00000" />
          </outcomes>{''.join(respconditions)}
        </resprocessing>
        <itemfeedback ident="correct" view="All">
          <flow_mat class="Block">
            <material>
              <mat_extension>
                <mat_formattedtext type="HTML">&lt;div style="font-family:'times new roman';font-size:11pt;color:#000000;font-weight:normal;"&gt;{escape_xml(feedback_text)}&lt;/div&gt;</mat_formattedtext>
              </mat_extension>
            </material>
          </flow_mat>
        </itemfeedback>
        <itemfeedback ident="incorrect" view="All">
          <flow_mat class="Block">
            <material>
              <mat_extension>
                <mat_formattedtext type="HTML">&lt;div style="font-family:'times new roman';font-size:11pt;color:#000000;font-weight:normal;"&gt;Incorrect. {escape_xml(feedback_text)}&lt;/div&gt;</mat_formattedtext>
              </mat_extension>
            </material>
          </flow_mat>
        </itemfeedback>
      </item>'''
        
        xml_parts.append(item_xml)
    
    xml_parts.append('''
    </section>
  </assessment>
</questestinterop>''')
    
    return '\ufeff' + ''.join(xml_parts)

def generate_manifest(title):
    """Generate imsmanifest.xml content."""
    return f'''\ufeff<?xml version="1.0" encoding="UTF-8"?>
<manifest xmlns:bb="http://www.blackboard.com/content-packaging/" identifier="man00001">
  <organizations default="toc00001">
    <organization identifier="toc00001" />
  </organizations>
  <resources>
    <resource bb:file="questions.dat" bb:title="{escape_xml(title)}" identifier="questions" type="assessment/x-bb-qti-pool" xml:base="questions" />
    <resource bb:file="categories.dat" bb:title="Categories" identifier="categories" type="course/x-bb-category" xml:base="categories" />
    <resource bb:file="itemcategories.dat" bb:title="Item Categories" identifier="itemcategories" type="course/x-bb-itemcategory" xml:base="itemcategories" />
    <resource bb:file="settings.dat" bb:title="Assessment Creation Settings" identifier="settings" type="course/x-bb-courseassessmentcreationsettings" xml:base="settings" />
  </resources>
</manifest>'''

def generate_categories():
    """Generate categories.dat content."""
    return '''\ufeff<?xml version="1.0" encoding="UTF-8"?>
<CATEGORIES>
</CATEGORIES>'''

def generate_itemcategories():
    """Generate itemcategories.dat content."""
    return '''\ufeff<?xml version="1.0" encoding="UTF-8"?>
<ITEMCATEGORIES>
</ITEMCATEGORIES>'''

def generate_settings():
    """Generate settings.dat content."""
    return '''\ufeff<?xml version="1.0" encoding="UTF-8"?>
<ASSESSMENTCREATIONSETTINGS>
  <ASSESSMENTCREATIONSETTING id="settings_1">
    <QTIASSESSMENTID value="assessment_1" />
    <ANSWERFEEDBACKENABLED>true</ANSWERFEEDBACKENABLED>
    <QUESTIONATTACHMENTSENABLED>false</QUESTIONATTACHMENTSENABLED>
    <ANSWERATTACHMENTSENABLED>false</ANSWERATTACHMENTSENABLED>
    <QUESTIONMETADATAENABLED>true</QUESTIONMETADATAENABLED>
    <DEFAULTPOINTVALUEENABLED>true</DEFAULTPOINTVALUEENABLED>
    <DEFAULTPOINTVALUE>1.0</DEFAULTPOINTVALUE>
    <ANSWERPARTIALCREDITENABLED>true</ANSWERPARTIALCREDITENABLED>
    <ANSWERRANDOMORDERENABLED>true</ANSWERRANDOMORDERENABLED>
    <ANSWERORIENTATIONENABLED>true</ANSWERORIENTATIONENABLED>
    <ANSWERNUMBEROPTIONSENABLED>true</ANSWERNUMBEROPTIONSENABLED>
  </ASSESSMENTCREATIONSETTING>
</ASSESSMENTCREATIONSETTINGS>'''

def generate_package_info():
    """Generate .bb-package-info content."""
    return 'cx.package.info.version=6.0'

def create_cartridge(md_file_path, output_dir=None):
    """Create a Jenzabar cartridge from a markdown file."""
    
    # Read markdown content
    with open(md_file_path, 'r', encoding='utf-8') as f:
        md_content = f.read()
    
    # Extract title from first line
    title_match = re.search(r'^#\s*(.+?)$', md_content, re.MULTILINE)
    if title_match:
        title = title_match.group(1).strip()
    else:
        title = os.path.splitext(os.path.basename(md_file_path))[0]
    
    # Clean title for filename
    safe_title = re.sub(r'[^\w\s-]', '', title).strip().replace(' ', '_')
    
    # Parse questions
    questions = parse_markdown_exam(md_content)
    
    print(f"Parsed {len(questions)} questions from {os.path.basename(md_file_path)}")
    
    # Count question types
    mc_count = sum(1 for q in questions if q['type'] == 'mc')
    ma_count = sum(1 for q in questions if q['type'] == 'ma')
    tf_count = sum(1 for q in questions if q['type'] == 'tf')
    print(f"  - Multiple Choice: {mc_count}")
    print(f"  - Multiple Answer (select all): {ma_count}")
    print(f"  - True/False: {tf_count}")
    
    # Generate output path
    if output_dir is None:
        output_dir = os.path.dirname(md_file_path) or '.'
    
    zip_filename = f"{safe_title}.zip"
    zip_path = os.path.join(output_dir, zip_filename)
    
    # Create zip file
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
        zf.writestr('questions.dat', generate_questions_dat(questions, title))
        zf.writestr('imsmanifest.xml', generate_manifest(title))
        zf.writestr('categories.dat', generate_categories())
        zf.writestr('itemcategories.dat', generate_itemcategories())
        zf.writestr('settings.dat', generate_settings())
        zf.writestr('.bb-package-info', generate_package_info())
    
    print(f"Created: {zip_path}")
    return zip_path

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python md_to_jenzabar.py <markdown_file.md> [output_directory]")
        sys.exit(1)
    
    md_file = sys.argv[1]
    output_dir = sys.argv[2] if len(sys.argv) > 2 else None
    
    create_cartridge(md_file, output_dir)
