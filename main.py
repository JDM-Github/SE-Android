import csv
import re
from collections import defaultdict

import joblib
from kivy.config import Config

WIDTH  = int(750  * 0.5) 
HEIGHT = int(1400 * 0.5) 
Config.set('graphics', 'width', WIDTH)
Config.set('graphics', 'height', HEIGHT)
Config.set('graphics', 'resizable', 0)
Config.write()

from kivy.utils import platform
from kivy.core.window import Window

if platform == "win":
	Window.size  = (WIDTH, HEIGHT)
	Window.top   = 30
	Window.left  = 1

from kivymd.app import MDApp
from kivy.uix.widget import Widget
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.graphics import Color, Ellipse, RoundedRectangle
from kivy.clock import Clock
from kivy.uix.popup import Popup
from kivymd.uix.filemanager import MDFileManager
from kivy.animation import Animation
from kivy.properties import NumericProperty, StringProperty

class MainWidget(Widget):

    positive_len = NumericProperty(0)
    negative_len = NumericProperty(0)
    neutral_len = NumericProperty(0)

    positive_percent = NumericProperty(0)
    negative_percent = NumericProperty(0)
    neutral_percent = NumericProperty(0)

    number_star_5 = StringProperty("0")
    number_star_4 = StringProperty("0")
    number_star_3 = StringProperty("0")
    number_star_2 = StringProperty("0")
    number_star_1 = StringProperty("0")

    result_text = StringProperty("NONE")
    result_color = StringProperty("#ffffff")

    max_percent_label = StringProperty("POSITIVE")
    max_percent = NumericProperty(0)

    full_comments_file = StringProperty("")
    category_name = StringProperty("NONE")
    subcategory_name = StringProperty("")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.current_index = 0
        self.sub_current_index = 0

    def on_image_click(self):
        self.open_file_manager()

    def open_file_manager(self):
        self.file_manager = MDFileManager(
            exit_manager=self.exit_file_manager,
            select_path=self.select_file,
        )
        self.file_manager.show('/')

    def select_file(self, path):
        if path.endswith('.csv'):
            self.full_comments_file = path
            print(f"File selected: {path}")
        else:
            self.show_error_popup("Invalid file type", "Please select a CSV file.")
        self.file_manager.close()

    def exit_file_manager(self, *args):
        self.file_manager.close()
    
    
    def simplify_text(self, text):
        """Simplifies text by removing numbers, punctuation, and stopwords."""
        return text.lower().replace(" ", "").strip()

    def categorize_columns(self, header):
        """Smart categorization of columns into categories."""
        category_map = defaultdict(list)
        current_category = None

        for col_name in header[4:]:
            simplified_name = self.simplify_text(col_name)

            if any(keyword in simplified_name for keyword in ["coordination", "gathered", "activity"]):
                current_category = "Coordination"
            elif any(keyword in simplified_name for keyword in ["objectives", "goals"]):
                current_category = "Objectives"
            elif any(keyword in simplified_name for keyword in ["feedback", "comment", "suggestion"]):
                current_category = "Feedback"
            elif any(keyword in simplified_name for keyword in ["discussions", "participation", "inputs"]):
                current_category = "Discussions"
            elif any(keyword in simplified_name for keyword in ["accessibility", "convenience", "comfort"]):
                current_category = "Accessibility"
            else:
                current_category = "Other" 
            category_map[current_category].append(col_name)

        return category_map

    def process_csv_to_3d_list(self, csv_file):
        result = []

        with open(csv_file, 'r', encoding='utf-8') as file:
            reader = csv.reader(file)
            header = next(reader)  
            category_map = self.categorize_columns(header)

            for row in reader:
                row_index = 4 
                for category, subcategories in category_map.items():
                    category_data = next((item for item in result if item["category"] == category), None)
                    if not category_data:
                        category_data = {"category": category, "subcategories": []}
                        result.append(category_data)

                    for subcat in subcategories:
                        if "Feedback" not in category:  
                            stars = int(row[row_index]) 
                            category_data["subcategories"].append({"subcategory": subcat, "stars": stars})
                        else:
                            feedback = row[row_index]
                            category_data["subcategories"].append({"subcategory": subcat, "text": feedback})
                        row_index += 1

        return result

    def aggregate_subcategories(self, subcategories):
        """Group subcategories and aggregate stars."""
        aggregated_data = defaultdict(lambda: [0, 0, 0, 0, 0]) 

        for item in subcategories:
            if not (item.get('stars') or not item.get('subcategory')):
                return {"subcategory": "NUN", "stars": [0, 0, 0, 0, 0]}

            subcategory = item['subcategory']
            stars = item['stars']
            aggregated_data[subcategory][stars - 1] += 1

        result = [
            {"subcategory": subcategory, "stars": counts}
            for subcategory, counts in aggregated_data.items()
        ]
        return result

    def open_csv(self):
        if not self.full_comments_file:
            self.show_error_popup("Invalid Submit", "File is missing.")
            print("INVALID SUBMIT")
            return

        model = joblib.load('naive_bayes_model.joblib')
        vectorizer = joblib.load('tfidf_vectorizer.joblib')
        encoder = joblib.load('label_encoder.joblib')
        try:
            with open(r"C:\JDM\SE\Copy of SSC Events' Evaluation Responses - CSL General Assembly 2024.csv", 'r', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                full_df = [row for row in reader]
        except Exception as e:
            self.show_error_popup("File Read Error", f"Error reading the file: {e}")
            return
    
        self.current_index = 0
        self.sub_current_index = 0
        self.structured_data = self.process_csv_to_3d_list(self.full_comments_file)

        if self.structured_data:
            self.category_name = self.structured_data[self.current_index].get('category', 'Unknown Category')
            
            self.sub_category_list = self.aggregate_subcategories(self.structured_data[self.current_index].get('subcategories', []))
            
            if self.sub_category_list:
                data = self.sub_category_list[self.sub_current_index]
                total_votes = sum(data['stars'])
                star_percentages = [(votes / total_votes) * 100 if total_votes > 0 else 0 for votes in data['stars']]
                
                self.subcategory_name = re.sub(r'^\d+\.\s*', '', data['subcategory'])
                self.subcategory_star = star_percentages

                self.number_star_1 = f"{data['stars'][0]}"
                self.number_star_2 = f"{data['stars'][1]}"
                self.number_star_3 = f"{data['stars'][2]}"
                self.number_star_4 = f"{data['stars'][3]}"
                self.number_star_5 = f"{data['stars'][4]}"

                stars = data['stars']
                total_votes = sum(stars)

                if total_votes > 0:
                    weighted_average = sum((i + 1) * stars[i] for i in range(5)) / total_votes
                else:
                    weighted_average = 0 

                if weighted_average >= 4.8:
                    self.result_text = "Very Satisfactory"
                    self.result_color = "#00FF00"
                elif 3.5 <= weighted_average < 4.8:
                    self.result_text = "Satisfactory"
                    self.result_color = "#FFA500"
                elif 2.5 <= weighted_average < 3.5:
                    self.result_text = "Needs Improvement"
                    self.result_color = "#FFCC00"
                else:
                    self.result_text = "Needs Enhancement"
                    self.result_color = "#FF0000" 

                colors = (237 / 255, 106 / 255, 110 / 255)
                for i, percentage in enumerate(star_percentages):
                    star_id = f"star_{i + 1}"
                    if hasattr(self.ids, star_id):
                        self.redraw_canvas(getattr(self.ids, star_id), colors, percentage)
                    else:
                        print(f"Warning: {star_id} does not exist in self.ids.")
            else:
                print("Warning: No subcategories available.")
        else:
            print("Warning: No data available in structured data.")

        target = None
        if full_df:
            for col in ['comment', 'comments', 'review', 'text']:
                for key in full_df[0].keys():
                    if col in key.lower():
                        target = [row[key] for row in full_df]
                        break
                if target:
                    break

            if target is None:
                print("Missing Column: The file must contain a 'comment, review, text' column.")
                return
        else:
            print("Missing Column: The file must contain a 'comment, review, text' column.")
            return

        predicted_sentiments = []
        for comment in target:
            transformed_comment = vectorizer.transform([comment])
            prediction_probabilities = model.predict_proba(transformed_comment)

            neutral_prob = prediction_probabilities[0][0] < 0.58 and prediction_probabilities[0][1] < 0.58

            if neutral_prob:
                sentiment = 'Neutral'
            else:
                prediction = model.predict(transformed_comment)
                sentiment = encoder.inverse_transform(prediction)[0]

            predicted_sentiments.append(sentiment)

        for i, row in enumerate(full_df):
            row['Predicted_Sentiment'] = predicted_sentiments[i]

        positive_comments = [row for row in full_df if row['Predicted_Sentiment'] == 'Positive']
        negative_comments = [row for row in full_df if row['Predicted_Sentiment'] == 'Negative']
        neutral_comments = [row for row in full_df if row['Predicted_Sentiment'] == 'Neutral']

        self.positive_len = len(positive_comments)
        self.negative_len = len(negative_comments)
        self.neutral_len = len(neutral_comments)

        total_comments = len(full_df)
        self.positive_percent = (self.positive_len / total_comments) * 100 if total_comments else 0
        self.neutral_percent = (self.neutral_len / total_comments) * 100 if total_comments else 0
        self.negative_percent = (self.negative_len / total_comments) * 100 if total_comments else 0

        self.redraw_canvas(self.ids.negative_bar, (237 / 255, 106 / 255, 110 / 255), self.negative_percent)
        self.redraw_canvas(self.ids.neutral_bar, (240 / 255, 137 / 255, 44 / 255), self.neutral_percent)
        self.redraw_canvas(self.ids.positive_bar, (134 / 255, 207 / 255, 111 / 255), self.positive_percent)

        percentages = {
            "POSITIVE": self.positive_percent,
            "NEUTRAL": self.neutral_percent,
            "NEGATIVE": self.negative_percent
        }

        self.max_percent_label = max(percentages, key=percentages.get)
        self.max_percent = int(percentages[self.max_percent_label])

        self.draw_pie_chart([self.negative_percent, self.neutral_percent, self.positive_percent])

    def prev_subcategory(self):
        if self.sub_current_index > 0:
            self.sub_current_index -= 1
        else:
            if self.current_index > 0:
                self.current_index -= 1
                self.sub_current_index = 0
            else:
                print("Warning: No previous category.")

        self.update_subcategory_data()

    def next_subcategory(self):
        if self.sub_current_index < len(self.sub_category_list) - 1:
            self.sub_current_index += 1
        else:
            if self.current_index < len(self.structured_data) - 1:
                self.current_index += 1
                self.sub_current_index = 0
            else:
                print("Warning: No next category.")
                return

        self.update_subcategory_data()

    def update_subcategory_data(self):
        if self.structured_data and self.current_index < len(self.structured_data):
            self.category_name = self.structured_data[self.current_index].get('category', 'Unknown Category')
            
            subcategories = self.structured_data[self.current_index].get('subcategories', [])
            self.sub_category_list = self.aggregate_subcategories(subcategories)
            
            if self.sub_category_list and 0 <= self.sub_current_index < len(self.sub_category_list):
                data = self.sub_category_list[self.sub_current_index]
                total_votes = sum(data['stars'])
                star_percentages = [(votes / total_votes) * 100 if total_votes > 0 else 0 for votes in data['stars']]
                
                self.subcategory_name = re.sub(r'^\d+\.\s*', '', data['subcategory'])
                self.subcategory_star = star_percentages

                self.number_star_1 = f"{data['stars'][0]}"
                self.number_star_2 = f"{data['stars'][1]}"
                self.number_star_3 = f"{data['stars'][2]}"
                self.number_star_4 = f"{data['stars'][3]}"
                self.number_star_5 = f"{data['stars'][4]}"

                stars = data['stars']
                total_votes = sum(stars)

                if total_votes > 0:
                    weighted_average = sum((i + 1) * stars[i] for i in range(5)) / total_votes
                else:
                    weighted_average = 0 

                if weighted_average >= 4.8:
                    self.result_text = "Very Satisfactory"
                    self.result_color = "#00FF00"
                elif 3.5 <= weighted_average < 4.8:
                    self.result_text = "Satisfactory"
                    self.result_color = "#FFA500"
                elif 2.5 <= weighted_average < 3.5:
                    self.result_text = "Needs Improvement"
                    self.result_color = "#FFCC00"
                else:
                    self.result_text = "Needs Enhancement"
                    self.result_color = "#FF0000" 

                colors = (237 / 255, 106 / 255, 110 / 255)
                for i, percentage in enumerate(star_percentages):
                    star_id = f"star_{i + 1}"
                    if hasattr(self.ids, star_id):
                        self.redraw_canvas(getattr(self.ids, star_id), colors, percentage)
                    else:
                        print(f"Warning: {star_id} does not exist in self.ids.")
            else:
                print("Warning: No subcategories available.")
        else:
            print("Warning: No data available in structured data.")
    
    # REDRAW THE BAR
    def redraw_canvas(self, widget, color, percent):
        widget.canvas.clear()
        with widget.canvas.before:
            Color(17/255,46/255,83/255)
            RoundedRectangle(size=widget.size, pos=widget.pos)

        def animate_rectangle(*args):
            widget.canvas.clear()
            with widget.canvas.before:
                Color(17 / 255, 46 / 255, 83 / 255)
                RoundedRectangle(size=widget.size, pos=widget.pos)

                Color(*color)
                # Draw the rectangle with initial size 0
                rect = RoundedRectangle(size=(0, widget.height), pos=widget.pos)

            # Create an animation to increase the size
            anim = Animation(size=(widget.width / 100 * percent, widget.height), duration=0.5)
            anim.start(rect)
        animate_rectangle()


    def draw_pie_chart(self, data):
        total = sum(data)
        colors = [
            (237 / 255, 106 / 255, 110 / 255),
            (240 / 255, 137 / 255, 44 / 255), 
            (134 / 255, 207 / 255, 111 / 255)]
    
        engagement = self.ids.engagement_pie
        engagement.canvas.clear()

        self.animate_pie(engagement, colors, 0, 0, data, total)
    

    # ANIMATION OF PIE CHART BEING DRAWN
    def animate_pie(self, engagement, colors, index, start_angle, data, total):
        if (index > 2):
            with engagement.canvas:
                Color(9 / 255, 25 / 255, 47 / 255)
                pie = Ellipse(
                    pos=(
                        (engagement.x + engagement.parent.width / 2 - 60 + engagement.width / 4) + engagement.width / 4,
                        (engagement.y - 40 + engagement.height / 4) + engagement.height / 4),
                    size=(1, 1)
                )
                Animation(size=(engagement.width / 2, engagement.height / 2),
                    pos=((engagement.x + engagement.parent.width / 2 - 60 + engagement.width / 4),
                        (engagement.y - 40 + engagement.height / 4)), duration=0.5).start(pie)
            return

        angle = 360 * (data[index] / total)
        with engagement.canvas:
            Color(*colors[index])
            pie_segment = Ellipse(
                pos=(engagement.x + engagement.parent.width / 2 - 60, engagement.y - 40),
                size=engagement.size,
                angle_start=start_angle,
                angle_end=start_angle
            )
        animation = Animation(angle_end=start_angle + angle, duration=0.5)
        start_angle += angle

        animation.bind(on_complete=lambda *_: self.animate_pie(engagement, colors, index+1, start_angle, data, total))
        animation.start(pie_segment)

    def show_error_popup(self, title, message):
        content = Label(text=message, size_hint=(1, 0.8), font_size="28sp", bold=True)
        close_button = Button(text="Close", size_hint=(1, 0.2), background_color=(9/255, 25/255, 47/255), bold=True)
        close_button.bind(on_release=self.close_popup)
        
        self.popup = Popup(content=content, size_hint=(0.8, 0.3))
        self.popup.content.add_widget(close_button)
        self.popup.open()

    def close_popup(self, instance):
        self.popup.dismiss()


class MainApp(MDApp):

    def build(self):
        Window.bind(on_drop_file=self._on_file_drop)
        self.main_widget = MainWidget()
        return self.main_widget

    def _on_file_drop(self, window, file_path, *args):
        decoded_path = file_path.decode('utf-8')
        if decoded_path.endswith('.csv'):
            self.main_widget.full_comments_file = decoded_path
        else:
            self.main_widget.show_error_popup("Invalid file type", "Please drop a .csv file.")
        return

if __name__ == "__main__":
    MainApp().run()
