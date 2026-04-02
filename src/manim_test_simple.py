"""Quick test of B&W comic style with Manim — no LaTeX needed."""
from manim import *

BG_COLOR = "#FAFAFA"
INK = "#1A1A1A"
LIGHT_INK = "#666666"


class ComicTest(Scene):
    def setup(self):
        self.camera.background_color = BG_COLOR

    def construct(self):
        # Title
        title = Text("Aristotle's World", color=INK, font_size=48, font="sans-serif")
        subtitle = Text("350 BC", color=LIGHT_INK, font_size=28, font="sans-serif")
        subtitle.next_to(title, DOWN, buff=0.3)
        self.play(Write(title), run_time=1)
        self.play(FadeIn(subtitle), run_time=0.5)
        self.wait(0.5)
        self.play(FadeOut(title), FadeOut(subtitle))

        # Aristotle character
        head = Circle(radius=0.5, color=INK, stroke_width=3, fill_opacity=0)
        left_eye = Dot(point=LEFT * 0.15 + UP * 0.08, radius=0.05, color=INK)
        right_eye = Dot(point=RIGHT * 0.15 + UP * 0.08, radius=0.05, color=INK)
        smile = Arc(radius=0.2, angle=-PI * 0.5, start_angle=-PI * 0.25,
                    color=INK, stroke_width=2).shift(DOWN * 0.12)
        beard = Arc(radius=0.3, angle=-PI * 0.7, start_angle=-PI * 0.15,
                    color=INK, stroke_width=2).shift(DOWN * 0.5)
        face = VGroup(head, left_eye, right_eye, smile, beard)

        # Body
        torso = Line(DOWN * 0.5, DOWN * 1.1, color=INK, stroke_width=3)
        left_arm = Line(DOWN * 0.65, DOWN * 0.9 + LEFT * 0.4, color=INK, stroke_width=2)
        right_arm = Line(DOWN * 0.65, DOWN * 0.9 + RIGHT * 0.4, color=INK, stroke_width=2)
        left_leg = Line(DOWN * 1.1, DOWN * 1.6 + LEFT * 0.25, color=INK, stroke_width=2)
        right_leg = Line(DOWN * 1.1, DOWN * 1.6 + RIGHT * 0.25, color=INK, stroke_width=2)
        # Toga lines
        toga1 = Line(DOWN * 0.55 + LEFT * 0.1, DOWN * 0.9 + RIGHT * 0.2, color=INK, stroke_width=1.5)
        toga2 = Line(DOWN * 0.55 + RIGHT * 0.1, DOWN * 0.85 + LEFT * 0.15, color=INK, stroke_width=1.5)
        body = VGroup(torso, left_arm, right_arm, left_leg, right_leg, toga1, toga2)

        aristotle = VGroup(face, body).move_to(LEFT * 3)
        label = Text("Aristotle", color=INK, font_size=22, font="sans-serif")
        label.next_to(aristotle, DOWN, buff=0.2)

        self.play(FadeIn(aristotle), FadeIn(label), run_time=1)
        self.wait(0.3)

        # Speech bubble
        speech_text = Text("Everything has\na natural place!", color=INK, font_size=24, font="sans-serif")
        speech_rect = SurroundingRectangle(
            speech_text, color=INK, stroke_width=2,
            corner_radius=0.25, buff=0.25, fill_color=BG_COLOR, fill_opacity=1,
        )
        pointer = Triangle(color=INK, stroke_width=2, fill_color=BG_COLOR, fill_opacity=1)
        pointer.scale(0.12).rotate(-PI / 2)
        pointer.next_to(speech_rect, LEFT, buff=-0.05)
        speech = VGroup(speech_rect, pointer, speech_text)
        speech.next_to(aristotle, RIGHT + UP, buff=0.3)

        self.play(FadeIn(speech), run_time=0.6)
        self.wait(1)
        self.play(FadeOut(speech), run_time=0.4)

        # Ball rolling
        ground = Line(LEFT * 6, RIGHT * 6, color=INK, stroke_width=2).shift(DOWN * 2)
        ball = Circle(radius=0.25, color=INK, stroke_width=3, fill_opacity=0)
        ball.move_to(LEFT * 4 + DOWN * 1.75)
        self.play(Create(ground), FadeIn(ball), run_time=0.5)

        # Motion lines
        lines = VGroup(*[
            Line(ball.get_left() + UP * (i - 1) * 0.15,
                 ball.get_left() + LEFT * 0.5 + UP * (i - 1) * 0.15,
                 color=LIGHT_INK, stroke_width=1.5)
            for i in range(3)
        ])

        self.play(
            ball.animate.move_to(RIGHT * 1 + DOWN * 1.75),
            FadeIn(lines),
            run_time=2,
            rate_func=rate_functions.ease_out_sine,
        )
        self.play(FadeOut(lines), run_time=0.3)

        # "It stops" text
        stops = Text("It stops.", color=INK, font_size=36, font="sans-serif")
        stops.next_to(ball, UP, buff=0.4)
        self.play(Write(stops), run_time=0.6)
        self.wait(0.5)

        # Question mark
        qmark = Text("?", color=INK, font_size=72, font="sans-serif")
        qmark.next_to(aristotle, UP + RIGHT, buff=0.1)
        self.play(FadeIn(qmark, scale=2), run_time=0.5)
        self.wait(1)

        # Four elements
        self.play(*[FadeOut(m) for m in [stops, qmark, ball, lines, ground]], run_time=0.5)

        elements_label = Text("The Four Elements", color=INK, font_size=32, font="sans-serif")
        elements_label.to_edge(UP, buff=0.5)
        self.play(Write(elements_label), run_time=0.6)

        # Earth circle, Water waves, Air dashed, Fire triangle
        earth = VGroup(
            Circle(radius=0.3, color=INK, stroke_width=3),
            Text("Earth", color=INK, font_size=16, font="sans-serif").shift(DOWN * 0.5)
        ).shift(LEFT * 3 + DOWN * 0.5)
        water = VGroup(
            *[Line(LEFT * 0.35 + UP * i * 0.12, RIGHT * 0.35 + UP * i * 0.12,
                   color=INK, stroke_width=2) for i in range(3)],
            Text("Water", color=INK, font_size=16, font="sans-serif").shift(DOWN * 0.5)
        ).shift(LEFT * 1 + DOWN * 0.5)
        air = VGroup(
            DashedVMobject(Circle(radius=0.3, color=INK, stroke_width=2), num_dashes=10),
            Text("Air", color=INK, font_size=16, font="sans-serif").shift(DOWN * 0.5)
        ).shift(RIGHT * 1 + DOWN * 0.5)
        fire = VGroup(
            Triangle(color=INK, stroke_width=3).scale(0.3),
            Text("Fire", color=INK, font_size=16, font="sans-serif").shift(DOWN * 0.5)
        ).shift(RIGHT * 3 + DOWN * 0.5)

        for elem, d in [(earth, DOWN), (water, DOWN), (air, UP), (fire, UP)]:
            self.play(FadeIn(elem), run_time=0.4)
            arr = Arrow(elem.get_center(), elem.get_center() + d * 0.8,
                        color=LIGHT_INK, stroke_width=2, max_tip_length_to_length_ratio=0.15)
            self.play(Create(arr), run_time=0.4)

        self.wait(1)

        # Cross out with "WRONG"
        wrong = Text("WRONG!", color="#CC0000", font_size=52, font="sans-serif", weight=BOLD)
        wrong.shift(DOWN * 2)
        cross_line1 = Line(LEFT * 5 + UP * 1, RIGHT * 5 + DOWN * 2, color="#CC0000", stroke_width=4)
        cross_line2 = Line(LEFT * 5 + DOWN * 2, RIGHT * 5 + UP * 1, color="#CC0000", stroke_width=4)
        self.play(Create(cross_line1), Create(cross_line2), FadeIn(wrong, scale=1.5), run_time=1)
        self.wait(1.5)

        self.play(*[FadeOut(m) for m in self.mobjects], run_time=0.8)
