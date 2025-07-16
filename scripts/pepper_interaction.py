# -*- coding: utf-8 -*-
from __future__ import print_function

# ===================================================================
#   PATH CONFIGURATION
# ===================================================================
import sys
import os

MODIM_SRC_PATH = '/home/robot/src/modim/src'
if not os.path.exists(MODIM_SRC_PATH):
    print("ERROR: The path to the MODIM library source is not correct.")
    sys.exit(1)
sys.path.append(MODIM_SRC_PATH)
sys.path.append(os.path.join(MODIM_SRC_PATH, 'GUI'))
# ===================================================================

# --- FRAMEWORK IMPORTS ---
from GUI.ws_client import ModimWSClient
from GUI.interaction_manager import InteractionManager

# ===================================================================
#   MAIN INTERACTION FUNCTION (SENT TO SERVER)
# ===================================================================
def interaction():
    """
    Feedback is based on the user's attention
    level, using the 'feedback_attentive' and 'feedback_distracted' actions.
    """
    # --- CONFIGURATION CONSTANTS AND DATA ---
    ATTENTION_LOG_FILE = 'attention_log.csv'
    ATTENTION_THRESHOLD = 0.60
    READING_TIME_SECONDS = 10

    SCIENCE_LESSONS = [
        {
            "announce_action":    "announce_photosynthesis",
            "explanation_action": "explanation_photosynthesis",
            "explanation_text":   "Photosynthesis is the process used by plants, algae and certain bacteria to harness energy from sunlight and turn it into chemical energy.",
            "question_action":    "question1",
            "correct_answer":     "sunlight",
            "topic_name":         "Photosynthesis"
        },
        {
            "announce_action":    "announce_solarsystem",
            "explanation_action": "explanation_solarsystem",
            "explanation_text":   "The solar system consists of the Sun and the objects that orbit it, including eight planets and numerous smaller bodies like asteroids and comets.",
            "question_action":    "question2",
            "correct_answer":     "the_sun",
            "topic_name":         "Solar system"
        },
        {
            "announce_action":    "announce_heart",
            "explanation_action": "explanation_heart",
            "explanation_text":   "The human heart is an organ that pumps blood throughout the body via the circulatory system, supplying oxygen and nutrients to the tissues and removing carbon dioxide and other wastes.",
            "question_action":    "question_heart",
            "correct_answer":     "heart",
            "topic_name":         "The Human Heart"
        }
    ]

    HISTORY_LESSONS = [
        {
            "announce_action":    "announce_rome",
            "explanation_action": "explanation_rome",
            "explanation_text":   "Ancient Rome was a civilization that grew from a small agricultural community founded on the Italian Peninsula in the 9th century BC into a vast empire.",
            "question_action":    "question_rome",
            "correct_answer":     "augustus",
            "topic_name":         "Ancient Rome"
        },
        {
            "announce_action":    "announce_egypt",
            "explanation_action": "explanation_egypt",
            "explanation_text":   "Ancient Egypt was a civilization in Northeast Africa. It is famous for its pharaohs, the great pyramids, and the Sphinx.",
            "question_action":    "question_egypt",
            "correct_answer":     "pyramids",
            "topic_name":         "Ancient Egypt"
        },
        {
            "announce_action":    "announce_columbus",
            "explanation_action": "explanation_columbus",
            "explanation_text":   "Christopher Columbus was an Italian explorer who completed four voyages across the Atlantic Ocean, opening the way for the widespread European exploration and colonization of the Americas.",
            "question_action":    "question_columbus",
            "correct_answer":     "columbus",
            "topic_name":         "Discovery of the Americas"
        }
    ]

    MATH_LESSONS = [
        {
            "announce_action":    "announce_pythagoras",
            "explanation_action": "explanation_pythagoras",
            "explanation_text":   "The Pythagorean theorem is a fundamental relation in geometry among the three sides of a right triangle. It states that the square of the hypotenuse is equal to the sum of the squares of the other two sides.",
            "question_action":    "question_pythagoras",
            "correct_answer":     "hypotenuse",
            "topic_name":         "Pythagorean Theorem"
        },
        {
            "announce_action":    "announce_pi",
            "explanation_action": "explanation_pi",
            "explanation_text":   "Pi is a mathematical constant, approximately equal to 3.14159. It is defined as the ratio of a circle's circumference to its diameter.",
            "question_action":    "question_pi",
            "correct_answer":     "pi",
            "topic_name":         "Pi (π)"
        },
        {
            "announce_action":    "announce_multiplication",
            "explanation_action": "explanation_multiplication",
            "explanation_text":   "Multiplication is another basic operation of arithmetic. The result of multiplying numbers is called the product.",
            "question_action":    "question_multiplication",
            "correct_answer":     "product",
            "topic_name":         "Multiplication"
        }
    ]

    MUSIC_LESSONS = [
        {
            "announce_action":    "announce_beethoven",
            "explanation_action": "explanation_beethoven",
            "explanation_text":   "Ludwig van Beethoven was a German composer and pianist. A crucial figure in the transition between the Classical and Romantic eras, he became famously deaf in his later life.",
            "question_action":    "question_beethoven",
            "correct_answer":     "beethoven",
            "topic_name":         "Beethoven"
        },
        {
            "announce_action":    "announce_piano",
            "explanation_action": "explanation_piano",
            "explanation_text":   "The piano is a keyboard instrument that produces sound by striking strings with hammers. A standard modern piano has 88 keys.",
            "question_action":    "question_piano",
            "correct_answer":     "piano",
            "topic_name":         "The Piano"
        },
        {
            "announce_action":    "announce_note",
            "explanation_action": "explanation_note",
            "explanation_text":   "In music, a note is a symbol denoting a musical sound. In English usage, a note is also the sound itself. Notes can represent the pitch and duration of a sound.",
            "question_action":    "question_note",
            "correct_answer":     "note",
            "topic_name":         "Musical Notes"
        }
    ]

    ALL_LESSONS_DATA = {
        "science": SCIENCE_LESSONS,
        "history": HISTORY_LESSONS,
        "math": MATH_LESSONS,
        "music": MUSIC_LESSONS
    }

    # --- UTILITY FUNCTIONS ---
    def load_attention_log(log_filename):
        import csv
        import os
        demo_path = im.path
        log_file_full_path = os.path.join(demo_path, 'scripts', log_filename)
        print("INFO: Attempting to load attention log from: %s" % log_file_full_path)
        if not os.path.exists(log_file_full_path):
            print("ERROR: '%s' not found." % log_filename)
            return None
        with open(log_file_full_path, 'r') as f:
            reader = csv.reader(f); next(reader); data = [row[1] for row in reader]
        print("INFO: Loaded %d labels." % len(data)); return data

    def was_user_attentive(attention_data, start_frame, num_frames, threshold):
        end_frame = start_frame + num_frames
        if end_frame > len(attention_data): end_frame = len(attention_data)
        if start_frame >= end_frame: return True
        segment = attention_data[start_frame:end_frame]
        attentive_count = segment.count('ATTENTIVE')
        total_count = len(segment)
        score = (float(attentive_count) / total_count) if total_count > 0 else 0
        score_percentage = int(score * 100)

        # 1. Send the specific command to update the progress bar in qaws.js
        im.executeModality('TEXT_attentionscore', str(score_percentage))

        # 2. Updates the main text shown to the user 
        im.executeModality('TEXT_default', "Your Attention Score: %d%%" % score_percentage)

        print("\n--- Attention score (frames %d-%d): %.2f%%" % (start_frame, end_frame, score * 100))
        return (score >= threshold, score_percentage)

    # --- CORE LOGIC SUB-FUNCTIONS ---
    def run_lesson_session(dependencies):
        import math
        import time

        attention_scores = []

        subject_name = dependencies.get("subject_name", "scienze")
        lessons = dependencies["current_lessons"]
        log_loader = dependencies["log_loader"]
        attention_checker = dependencies["attention_checker"]
        attention_log_file = dependencies["attention_log_file"]
        threshold = dependencies["threshold"]
        reading_time = dependencies["reading_time"]

        attention_data = log_loader(attention_log_file)
        if attention_data is None:
            im.executeModality('TEXT_default', "Error: I cannot start the lesson, my learning materials are missing.")
            return

        learned_topics = []
        num_lessons = len(lessons)
        total_frames = len(attention_data)
        block_size = int(math.ceil(total_frames / float(num_lessons))) if num_lessons > 0 else 0

        current_topic_index = 0
        for i in range(num_lessons):
            if current_topic_index >= num_lessons:
                im.executeModality('TEXT_default', "Congratulations, you've completed all the topics!")
                break

            lesson = lessons[current_topic_index]
            start_frame_block = i * block_size

            # --- RESET THE ATTENTION BAR FOR NEW TOPIC ---
            im.executeModality('TEXT_attentionscore', '0')

            # 1) Topic announcement
            im.execute(lesson["announce_action"])
            time.sleep(3)

            # 2) Explanation and text
            im.execute(lesson["explanation_action"])
            time.sleep(reading_time)

            # 3) Calculate and show attention Score
            is_attentive, score_percentage = attention_checker(attention_data, start_frame_block, block_size, threshold)
            attention_scores.append(score_percentage)
            time.sleep(3)

            # 4) Question to the student
            answer = im.ask(lesson["question_action"], timeout=15)

            # 5) Evaluate the answer
            is_correct      = answer and (lesson["correct_answer"].lower() in answer.lower())
            is_last_block   = (i == num_lessons - 1)

            # keep track of mastered topics
            if is_correct:
                learned_topics.append(lesson["topic_name"])

            # ------- feedback to the student -------
            if is_correct:
                im.executeModality('TEXT_default', "Correct answer! Well done.")
                if lesson["topic_name"] not in learned_topics:    
                    learned_topics.append(lesson["topic_name"])
                current_topic_index += 1
            else:
                im.executeModality('TEXT_default', "Wrong answer. Let’s review this topic.")

            time.sleep(3)

            # 6) Feedback based on attention
            if is_attentive:
                im.execute("feedback_attentive")
            else:
                im.execute("feedback_distracted")
            time.sleep(3)


        # Final summary of lessons completed
        if learned_topics:
            msg = "You learned: " + ", ".join(learned_topics)
        else:
            msg = "There are no successfully completed topics."

        im.executeModality('TEXT_default', msg)
        time.sleep(5)        

        if attention_scores:
            avg_score = sum(attention_scores) / len(attention_scores)
            im.executeModality('TEXT_default', "Your average attention was: {:.0f}%".format(avg_score))
            print("DEBUG - Attention Scores:", attention_scores)
            print("DEBUG - Average:", avg_score)
        else:
            im.executeModality('TEXT_default', "No attention data available.")


        print("DEBUG - Attention Scores:", attention_scores)
        print("DEBUG - Average:", sum(attention_scores) / len(attention_scores))


        im.executeModality(
            'TEXT_default',
            "Today's {} class ends here. We'll return to the menu in a few seconds..."
            .format(subject_name)
        )

        # --- RESET THE WARNING BAR AT THE END OF THE LESSON ---
        im.executeModality('TEXT_attentionscore', '0')

        time.sleep(5)          # hold the goodbye message


    def run_subject_menu(dependencies):
        # Get the master dictionary from the dependencies
        all_lessons = dependencies["all_lessons_data"]

        while True:
            choice = im.ask("menu_subjects", timeout=20)

            if choice in all_lessons:
                dependencies["subject_name"] = choice
                dependencies["current_lessons"] = all_lessons[choice] 
                dependencies["lesson_runner"](dependencies)
                
            elif choice in ("back", "timeout"):
                im.executeModality('TEXT_default', "Returning to the main menu.")
                break
            else:
                im.executeModality('TEXT_default', "I didn't understand. Please choose an option.")

    def run_general_quiz():
        im.execute("quiz_placeholder")

    def start_interaction_controller(dependencies):
        import time
        while True:
            choice = im.ask("welcome_educational_quiz", timeout=30)
            if choice == "lessons":
                dependencies["subject_menu_runner"](dependencies)
            elif choice == "quiz":
                dependencies["quiz_runner"]()
            elif choice in ("exit", "timeout"):
                break
            else:
                im.executeModality('TEXT_default', "Sorry, I didn't get that. Please choose an option from the menu.")
            time.sleep(1)

        im.execute("goodbye")
        print("--- Remote Script Execution Finished ---")

    # --- DICTIONARY OF ALL DEPENDENCIES ---
    app_dependencies = {
        "log_loader": load_attention_log,
        "attention_checker": was_user_attentive,
        "attention_log_file": ATTENTION_LOG_FILE,
        "threshold": ATTENTION_THRESHOLD,
        "reading_time": READING_TIME_SECONDS,
        "lesson_runner": run_lesson_session,           
        "subject_menu_runner": run_subject_menu,
        "quiz_runner": run_general_quiz,
        "all_lessons_data": ALL_LESSONS_DATA, 

        # This will be populated later by run_subject_menu
        "current_lessons": None, 
        "subject_name": None
    }

    # --- FINAL ENTRY POINT ---
    start_interaction_controller(app_dependencies)

# ===================================================================
#   CLIENT-SIDE EXECUTION BLOCK
# ===================================================================
if __name__ == '__main__':
    print("--- Starting Client to connect to MODIM Server ---")
    mws = ModimWSClient()
    DEMO_ROOT_PATH = '/home/robot/src/modim/demo/sample'
    mws.setDemoPath(DEMO_ROOT_PATH)
    print("INFO: Manually setting server Demo Path to: %s" % DEMO_ROOT_PATH)
    mws.run_interaction(interaction)
    print("--- Execution finished. Client disconnected. ---")
