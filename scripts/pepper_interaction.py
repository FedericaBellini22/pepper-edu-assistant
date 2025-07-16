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
            "announce_action":    "announce_watercycle",
            "explanation_action": "explanation_watercycle",
            "explanation_text":   "The water cycle describes how water evaporates from the surface of the Earth, rises into the atmosphere, cools and condenses into rain or snow in clouds, and falls again to the surface.",
            "question_action":    "question3",
            "correct_answer":     "precipitation",
            "topic_name":         "Water cycle"
        }
    ]

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

        im.executeModality('TEXT_default', "Your Attention Score: %d%%" % score_percentage)

        print("\n--- Attention score (frames %d-%d): %.2f%%" % (start_frame, end_frame, score * 100))
        return (score >= threshold, score_percentage)

    # --- CORE LOGIC SUB-FUNCTIONS ---
    def run_science_lessons(dependencies):
        import math
        import time

        attention_scores = []

        subject_name = dependencies.get("subject_name", "scienze")
        lessons = dependencies["lessons"]
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
        while True:
            choice = im.ask("menu_subjects", timeout=20)
            if choice == "science":
                dependencies["subject_name"] = "science"
                dependencies["science_runner"](dependencies)
            elif choice == "history":
                dependencies["subject_name"] = "history"
                im.execute("history_placeholder")
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
        "lessons": SCIENCE_LESSONS,
        "log_loader": load_attention_log,
        "attention_checker": was_user_attentive,
        "attention_log_file": ATTENTION_LOG_FILE,
        "threshold": ATTENTION_THRESHOLD,
        "reading_time": READING_TIME_SECONDS,
        "science_runner": run_science_lessons,
        "subject_menu_runner": run_subject_menu,
        "quiz_runner": run_general_quiz,
        "history_placeholder_runner": run_general_quiz,
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
