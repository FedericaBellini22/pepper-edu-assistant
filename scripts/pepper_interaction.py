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
    import os
    PEPPER_IP   = os.environ.get('PEPPER_IP', '192.168.1.100')
    PEPPER_PORT = int(os.environ.get('PEPPER_PORT', '9559'))
    PEPPER_LANG = os.environ.get('PEPPER_LANG', 'Italian')
    PEPPER_VOL  = float(os.environ.get('PEPPER_VOL', '0.8'))
    PEPPER_SPD  = int(os.environ.get('PEPPER_SPD', '90'))
    PEPPER_TOOLS_HOME = os.getenv('PEPPER_TOOLS_HOME')

    def _build_robot_say():
        # 1) prova pepper_cmd se presente
        try:
            if PEPPER_TOOLS_HOME:
                import sys as _sys, os as _os
                _sys.path.append(os.path.join(PEPPER_TOOLS_HOME, 'cmd_server'))
            import pepper_cmd
            from pepper_cmd import robot as _pc_robot
            try:
                try: pepper_cmd.end()
                except: pass
                try: pepper_cmd.begin()
                except: pass
                try: _pc_robot.tts_service.setLanguage(PEPPER_LANG)
                except: pass
            except:  # inizializzazione soft
                pass

            def _say_pc(text, speed=None, volume=None):
                try:
                    _pc_robot.asay(text)
                except:
                    pass
            return _say_pc
        except:
            pass

        # 2) fallback NAOqi ufficiale (qi / ALProxy)
        _tts = None
        try:
            import qi
            _session = qi.Session()
            _session.connect("tcp://%s:%d" % (PEPPER_IP, PEPPER_PORT))
            _tts = _session.service("ALTextToSpeech")
        except:
            try:
                from naoqi import ALProxy
                _tts = ALProxy("ALTextToSpeech", PEPPER_IP, PEPPER_PORT)
            except:
                _tts = None

        if _tts:
            try: _tts.setLanguage(PEPPER_LANG)
            except: pass
            try: _tts.setVolume(PEPPER_VOL)
            except: pass
            try: _tts.setParameter("speed", PEPPER_SPD)
            except: pass

            def _say_naoqi(text, speed=None, volume=None):
                try:
                    prefix = ""
                    if volume is not None:
                        v = max(0, min(100, int(volume)))
                        prefix += "\\vol=%d\\" % v
                    if speed is not None:
                        s = max(50, min(200, int(speed)))
                        prefix += "\\rspd=%d\\" % s
                    _tts.say("%s %s" % (prefix, text))
                except:
                    pass
            return _say_naoqi

        # 3) nessun TTS disponibile: no-op
        def _noop(*args, **kwargs): 
            pass
        return _noop

    global robot_say
    robot_say = _build_robot_say()

    def _build_robot_gesture():
        # 1) pepper_cmd se disponibile
        try:
            if PEPPER_TOOLS_HOME:
                import sys as _sys, os as _os
                _sys.path.append(os.path.join(PEPPER_TOOLS_HOME, 'cmd_server'))
            import pepper_cmd
            from pepper_cmd import robot as _pc_robot
            def _run(anim_id, async_run=True):
                try:
                    if async_run:
                        _pc_robot.animation_player_service.post.run(anim_id)  # async corretto
                    else:
                        _pc_robot.animation_player_service.run(anim_id)
                    return True
                except Exception:
                    return False
            return _run
        except Exception:
            pass

        # 2) fallback NAOqi (qi) -> ALAnimationPlayer
        try:
            import qi
            _session = qi.Session()
            _session.connect("tcp://%s:%d" % (PEPPER_IP, PEPPER_PORT))
            _anim = _session.service("ALAnimationPlayer")
            def _run(anim_id, async_run=True):
                try:
                    if async_run:
                        _anim.post.run(anim_id)   # async in NAOqi
                    else:
                        _anim.run(anim_id)
                    return True
                except Exception:
                    return False
            return _run
        except Exception:
            def _noop(*args, **kwargs): return False
            return _noop

    global robot_gesture
    robot_gesture = _build_robot_gesture()

    GESTURES = {
        "happy":   "animations/Stand/Gestures/Happy_1",
        "no":      "animations/Stand/Gestures/No_1",
        "yes":     "animations/Stand/Gestures/Yes_1",
        "explain": "animations/Stand/Gestures/Explain_1",
        "hey":     "animations/Stand/Gestures/Hey_1",
    }

    def _make_play_gesture(gesture_map, runner):
        def _play(key, async_run=True):
            anim = gesture_map.get(key)
            if not anim:
                return False
            try:
                return runner(anim, async_run)
            except Exception:
                return False
        return _play

    play_gesture = _make_play_gesture(GESTURES, robot_gesture)

    def robot_show_url(url):
        try:
            import qi, os
            session = qi.Session()
            session.connect("tcp://%s:%d" % (os.environ.get('PEPPER_IP'), int(os.environ.get('PEPPER_PORT','9559'))))
            tablet = session.service("ALTabletService")
            tablet.showWebview()
            tablet.loadUrl(url)
        except Exception as e:
            print("Tablet loadUrl error:", e)

    # subito dopo aver definito robot_show_url(...) e prima dei menu:
    tablet_url = "http://<IP_DEL_MIO_PC>:8000/index.html"   # o la pagina display MODIM corretta
    robot_show_url(tablet_url)


    # === GESTURES HELPERS (inside interaction) ===
    def _get_session():
        import qi
        s = qi.Session()
        s.connect("tcp://%s:%d" % (PEPPER_IP, PEPPER_PORT))
        return s


    """
    Feedback is based on the user's attention
    level, using the 'feedback_attentive' and 'feedback_distracted' actions.
    """
    # --- CONFIGURATION CONSTANTS AND DATA ---
    ATTENTION_LOG_FILE = 'attention_mixed_distracted.csv'
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
            "announce_action":    "announce_prime",
            "explanation_action": "explanation_prime",
            "explanation_text":   "A prime number is a natural number greater than 1 that has no positive divisors other than 1 and itself. For example, 2, 3, 5, and 7 are prime numbers.",
            "question_action":    "question_prime",
            "correct_answer":     "prime",
            "topic_name":         "Prime Numbers"
        },
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
            "announce_action":    "announce_mozart",
            "explanation_action": "explanation_mozart",
            "explanation_text":   "Wolfgang Amadeus Mozart was a prolific and influential composer of the Classical period. He was a child prodigy who composed his first piece of music at age five.",
            "question_action":    "question_mozart",
            "correct_answer":     "mozart",
            "topic_name":         "Mozart"
        },
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
        if end_frame > len(attention_data):
            end_frame = len(attention_data)
        if start_frame >= end_frame:
            im.executeModality('TEXT_attentionscore', '100')
            im.executeModality('TEXT_default', "Your Attention Score: 100%")
            return (True, 100)

        segment = attention_data[start_frame:end_frame]
        attentive_count = segment.count('ATTENTIVE')
        total_count = len(segment)
        score = (float(attentive_count) / total_count) if total_count > 0 else 0
        score_percentage = int(score * 100)

        im.executeModality('TEXT_attentionscore', str(score_percentage))
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
        quiz_runner = dependencies["quiz_runner"]
        pg = dependencies.get("play_gesture")

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
            #play_gesture("explain")
            robot_say("Adesso parliamo di %s." % lesson["topic_name"])
            time.sleep(3)

            # 2) Explanation and text
            im.execute(lesson["explanation_action"])
            robot_say("Per favore leggi sul tablet. Tra poco ti farò una domanda.")
            time.sleep(reading_time)

            # 3) Calculate and show attention Score
            is_attentive, score_percentage = attention_checker(attention_data, start_frame_block, block_size, threshold)
            attention_scores.append(score_percentage)
            if score_percentage >= int(threshold * 100):
                robot_say("Ottima attenzione, continua così!")
                if pg: pg("yes")
            else:
                robot_say("Attenzione un po' bassa, prova a concentrarti di più.")
                if pg: pg("no")


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
                robot_say("Risposta corretta, bravo!")
                if pg: pg("happy")
                if lesson["topic_name"] not in learned_topics:    
                    learned_topics.append(lesson["topic_name"])
                current_topic_index += 1
            else:
                im.executeModality('TEXT_default', "Wrong answer. Let’s review this topic.")
                robot_say("Non è corretto. Rivediamo insieme.")
                if pg: pg("no")

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
            robot_say("La tua attenzione media è stata del %d per cento." % int(avg_score))
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
        robot_say("La lezione di %s termina qui. Torniamo al menu tra poco." % subject_name)
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

    def run_general_quiz(dependencies):
        import time
        import random

        all_lessons = dependencies["all_lessons_data"]

        topics = {
            "Science": random.choice(all_lessons["science"]),
            "History": random.choice(all_lessons["history"]),
            "Math": random.choice(all_lessons["math"]),
            "Music": random.choice(all_lessons["music"])
        }


        correct_count = 0
        total = len(topics)

        im.executeModality('TEXT_default', "Let's begin the general knowledge quiz!")
        robot_say("Iniziamo il quiz di cultura generale.")
        if pg: pg("hey")
        time.sleep(2)

        for subject, lesson in topics.items():
            im.executeModality('TEXT_default', "Category: {}".format(subject))
            robot_say("Categoria: %s." % subject)
            time.sleep(1)

            im.execute(lesson["announce_action"])
            time.sleep(2)

            answer = im.ask(lesson["question_action"], timeout=15)

            if answer and lesson["correct_answer"].lower() in answer.lower():
                im.executeModality('TEXT_default', "Correct answer! Well done.")
                correct_count += 1
            else:
                im.executeModality(
                    'TEXT_default',
                    "Wrong. The correct answer was '{}'.".format(lesson['correct_answer'])
                )
            time.sleep(2)

        score_percent = int((correct_count / float(total)) * 100)
        final_msg = "You scored {} out of {} ({}%).".format(correct_count, total, score_percent)
        im.executeModality('TEXT_default', final_msg)
        robot_say("Hai totalizzato %d su %d." % (correct_count, total))
        time.sleep(3)

        if score_percent == 100:
            im.executeModality('TEXT_default', "Excellent work! You're a true knowledge master!")
        elif score_percent >= 75:
            im.executeModality('TEXT_default', "Great job! Keep it up!")
        elif score_percent >= 50:
            im.executeModality('TEXT_default', "Not bad! But you can do better with some revision.")
        else:
            im.executeModality('TEXT_default', "Keep practicing and you'll improve!")
        time.sleep(3)



    def start_interaction_controller(dependencies):
        import time
        while True:
            choice = im.ask("welcome_educational_quiz", timeout=30)
            if choice == "lessons":
                robot_say("Apro il menu delle lezioni.")
                dependencies["subject_menu_runner"](dependencies)
            elif choice == "quiz":
                robot_say("Preparati al quiz.")
                dependencies["quiz_runner"](dependencies)
            elif choice in ("exit", "timeout"):
                break
            else:
                im.executeModality('TEXT_default', "Sorry, I didn't get that. Please choose an option from the menu.")
            time.sleep(1)

        im.execute("goodbye")
        robot_say("Alla prossima! È stato un piacere lavorare con te.")
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
        "play_gesture": play_gesture,

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