"""
Prototype: Render ep01 Scene 1 (Aristotle's World) with Manim.
Tests the B&W comic line art approach.

Run: manim -pql src/manim_prototype.py AristotleScene
  -p = preview (open after render)
  -ql = quality low (480p, fast for testing)
  -qh = quality high (1080p, for production)
"""
from manim import *


# ── B&W Comic Style Config ──
BG_COLOR = "#FAFAFA"
INK = "#1A1A1A"
LIGHT_INK = "#666666"
ACCENT = "#444444"


class ComicStyle:
    """Reusable style helpers for B&W comic line art."""

    @staticmethod
    def character_head(radius=0.6, **kwargs):
        """Simple cartoon head — circle with face."""
        head = Circle(radius=radius, color=INK, stroke_width=3, fill_opacity=0)
        # Eyes: two dots
        left_eye = Dot(point=head.get_center() + LEFT * radius * 0.3 + UP * radius * 0.15,
                       radius=0.06, color=INK)
        right_eye = Dot(point=head.get_center() + RIGHT * radius * 0.3 + UP * radius * 0.15,
                        radius=0.06, color=INK)
        # Smile: small arc
        smile = Arc(radius=radius * 0.3, angle=-PI * 0.6, start_angle=-PI * 0.2,
                    color=INK, stroke_width=2)
        smile.move_to(head.get_center() + DOWN * radius * 0.2)
        return VGroup(head, left_eye, right_eye, smile)

    @staticmethod
    def stick_body(head_bottom, height=1.2):
        """Simple stick figure body below a head."""
        start = head_bottom
        # Torso
        torso_end = start + DOWN * height * 0.5
        torso = Line(start, torso_end, color=INK, stroke_width=3)
        # Arms
        arm_start = start + DOWN * height * 0.15
        left_arm = Line(arm_start, arm_start + LEFT * 0.4 + DOWN * 0.3, color=INK, stroke_width=2)
        right_arm = Line(arm_start, arm_start + RIGHT * 0.4 + DOWN * 0.3, color=INK, stroke_width=2)
        # Legs
        left_leg = Line(torso_end, torso_end + LEFT * 0.3 + DOWN * height * 0.4, color=INK, stroke_width=2)
        right_leg = Line(torso_end, torso_end + RIGHT * 0.3 + DOWN * height * 0.4, color=INK, stroke_width=2)
        return VGroup(torso, left_arm, right_arm, left_leg, right_leg)

    @staticmethod
    def aristotle(position=ORIGIN):
        """Aristotle: beard, toga drape lines."""
        head = ComicStyle.character_head(radius=0.5)
        # Beard: small arc below chin
        beard = Arc(radius=0.3, angle=-PI * 0.8, start_angle=-PI * 0.1,
                    color=INK, stroke_width=2)
        beard.move_to(head.get_center() + DOWN * 0.55)
        # Simple toga lines
        body = ComicStyle.stick_body(head.get_bottom(), height=1.0)
        toga_line1 = Line(head.get_bottom() + LEFT * 0.1,
                         head.get_bottom() + DOWN * 0.5 + RIGHT * 0.3,
                         color=INK, stroke_width=2)
        toga_line2 = Line(head.get_bottom() + RIGHT * 0.1,
                         head.get_bottom() + DOWN * 0.4 + LEFT * 0.2,
                         color=INK, stroke_width=2)
        char = VGroup(head, beard, body, toga_line1, toga_line2)
        char.move_to(position)
        return char

    @staticmethod
    def newton(position=ORIGIN):
        """Newton: big curly wig, formal coat."""
        head = ComicStyle.character_head(radius=0.5)
        # Wig: wavy bumps around head
        wig_points = []
        for angle in range(30, 330, 20):
            r = 0.65 + 0.08 * (1 if angle % 40 == 0 else -1)
            x = r * np.cos(angle * DEGREES)
            y = r * np.sin(angle * DEGREES)
            wig_points.append(head.get_center() + np.array([x, y, 0]))
        if len(wig_points) >= 3:
            wig = VMobject(color=INK, stroke_width=2)
            wig.set_points_smoothly(wig_points)
        else:
            wig = Circle(radius=0.65, color=INK, stroke_width=2)
            wig.move_to(head.get_center())
        body = ComicStyle.stick_body(head.get_bottom(), height=1.0)
        char = VGroup(wig, head, body)
        char.move_to(position)
        return char

    @staticmethod
    def speech_bubble(text, direction=RIGHT, width=4):
        """Comic-style speech bubble with pointer."""
        bubble_text = Text(text, color=INK, font_size=28, font="sans-serif")
        bubble_rect = SurroundingRectangle(
            bubble_text, color=INK, stroke_width=2,
            corner_radius=0.3, buff=0.3, fill_color=BG_COLOR, fill_opacity=1,
        )
        # Pointer triangle
        pointer = Triangle(color=INK, stroke_width=2, fill_color=BG_COLOR, fill_opacity=1)
        pointer.scale(0.15)
        pointer.next_to(bubble_rect, -direction, buff=-0.05)
        return VGroup(bubble_rect, pointer, bubble_text)

    @staticmethod
    def thought_bubble(text, width=3):
        """Comic thought bubble with trailing circles."""
        bubble_text = Text(text, color=INK, font_size=24, font="sans-serif")
        bubble = Ellipse(
            width=bubble_text.width + 0.8, height=bubble_text.height + 0.6,
            color=INK, stroke_width=2, fill_color=BG_COLOR, fill_opacity=1,
        )
        bubble.move_to(bubble_text)
        # Trailing dots
        dot1 = Circle(radius=0.08, color=INK, stroke_width=1.5,
                      fill_color=BG_COLOR, fill_opacity=1)
        dot1.next_to(bubble, DOWN + LEFT, buff=0.1)
        dot2 = Circle(radius=0.05, color=INK, stroke_width=1.5,
                      fill_color=BG_COLOR, fill_opacity=1)
        dot2.next_to(dot1, DOWN + LEFT, buff=0.08)
        return VGroup(bubble, dot1, dot2, bubble_text)

    @staticmethod
    def motion_lines(start, direction=RIGHT, count=3, length=0.8):
        """Comic speed/motion lines."""
        lines = VGroup()
        for i in range(count):
            offset = UP * (i - count / 2) * 0.2
            line = Line(
                start + offset,
                start + offset + direction * length,
                color=LIGHT_INK, stroke_width=2,
            )
            lines.add(line)
        return lines


class AristotleScene(Scene):
    """
    EP01 Scene 1: Aristotle's World — "Why do things move?"

    Demonstrates the B&W comic style with:
    - Character appearing
    - Objects animating
    - Equations revealed
    - Speech/thought bubbles
    - Motion lines
    """

    def setup(self):
        self.camera.background_color = BG_COLOR

    def construct(self):
        # ── Scene title ──
        title = Text("Aristotle's World", color=INK, font_size=48, font="sans-serif")
        subtitle = Text("350 BC", color=LIGHT_INK, font_size=28, font="sans-serif")
        subtitle.next_to(title, DOWN, buff=0.3)
        self.play(Write(title), run_time=1)
        self.play(FadeIn(subtitle), run_time=0.5)
        self.wait(1)
        self.play(FadeOut(title), FadeOut(subtitle))

        # ── Aristotle enters ──
        aristotle = ComicStyle.aristotle(position=LEFT * 4)
        label = Text("Aristotle", color=INK, font_size=24, font="sans-serif")
        label.next_to(aristotle, DOWN, buff=0.2)

        self.play(
            aristotle.animate.move_to(LEFT * 2.5),
            FadeIn(label),
            run_time=1.5,
        )
        self.wait(0.5)

        # ── "Everything has a natural place" ──
        speech = ComicStyle.speech_bubble(
            "Everything has\na natural place!",
            direction=LEFT, width=4,
        )
        speech.next_to(aristotle, RIGHT + UP, buff=0.3)
        self.play(FadeIn(speech), run_time=0.8)
        self.wait(1.5)
        self.play(FadeOut(speech), run_time=0.5)

        # ── Four elements demo ──
        elements_title = Text("The Four Elements", color=INK, font_size=32, font="sans-serif")
        elements_title.to_edge(UP, buff=0.5)
        self.play(Write(elements_title), run_time=0.8)

        # Earth (heavy, falls) — simple rock shape
        earth = VGroup(
            Circle(radius=0.3, color=INK, stroke_width=3),
            Text("Earth", color=INK, font_size=18, font="sans-serif").shift(DOWN * 0.5),
        ).shift(LEFT * 3 + DOWN * 0.5)

        # Water — wavy lines
        water = VGroup(
            *[Line(LEFT * 0.4 + UP * i * 0.15, RIGHT * 0.4 + UP * i * 0.15,
                   color=INK, stroke_width=2).shift(DOWN * 0.3)
              for i in range(3)],
            Text("Water", color=INK, font_size=18, font="sans-serif").shift(DOWN * 0.7),
        ).shift(LEFT * 1)

        # Air — dashed circle
        air = VGroup(
            DashedVMobject(Circle(radius=0.3, color=INK, stroke_width=2), num_dashes=12),
            Text("Air", color=INK, font_size=18, font="sans-serif").shift(DOWN * 0.5),
        ).shift(RIGHT * 1)

        # Fire — triangle
        fire = VGroup(
            Triangle(color=INK, stroke_width=3, fill_opacity=0).scale(0.35),
            Text("Fire", color=INK, font_size=18, font="sans-serif").shift(DOWN * 0.5),
        ).shift(RIGHT * 3)

        for elem, direction in [(earth, DOWN), (water, DOWN), (air, UP), (fire, UP)]:
            self.play(FadeIn(elem), run_time=0.5)
            arrow = Arrow(
                elem.get_center(),
                elem.get_center() + direction * 1.0,
                color=ACCENT, stroke_width=2, max_tip_length_to_length_ratio=0.2,
            )
            self.play(Create(arrow), run_time=0.5)

        self.wait(1)

        # ── Clear and show ball rolling ──
        self.play(
            *[FadeOut(m) for m in self.mobjects if m != aristotle and m != label],
            run_time=0.8,
        )

        # ── Ball rolling demo ──
        ground = Line(LEFT * 6, RIGHT * 6, color=INK, stroke_width=2).shift(DOWN * 1.5)
        ball = Circle(radius=0.25, color=INK, stroke_width=3, fill_opacity=0)
        ball.move_to(LEFT * 4 + DOWN * 1.25)

        self.play(Create(ground), FadeIn(ball), run_time=0.5)

        # Ball rolls right with motion lines
        motion = ComicStyle.motion_lines(ball.get_left(), direction=LEFT, count=3, length=0.6)

        self.play(
            ball.animate.move_to(RIGHT * 2 + DOWN * 1.25),
            FadeIn(motion),
            run_time=2,
            rate_func=rate_functions.ease_out_sine,
        )
        self.play(FadeOut(motion), run_time=0.3)

        # Ball stops — "It stops" text
        stops_text = Text("It stops.", color=INK, font_size=36, font="sans-serif")
        stops_text.next_to(ball, UP, buff=0.5)
        self.play(Write(stops_text), run_time=0.8)
        self.wait(1)

        # ── Aristotle's question ──
        thought = ComicStyle.thought_bubble("But WHY\ndoes it stop?")
        thought.next_to(aristotle, RIGHT + UP, buff=0.2)
        self.play(FadeIn(thought), run_time=0.8)
        self.wait(1.5)

        # ── Equation reveal ──
        self.play(
            *[FadeOut(m) for m in self.mobjects],
            run_time=0.8,
        )

        eq_label = Text("Aristotle believed:", color=LIGHT_INK, font_size=28, font="sans-serif")
        eq_label.to_edge(UP, buff=1)
        equation = MathTex(r"F_{\text{push}} > 0 \implies \text{motion}", color=INK, font_size=44)
        equation.next_to(eq_label, DOWN, buff=0.5)

        anti_eq = MathTex(r"F_{\text{push}} = 0 \implies \text{rest}", color=INK, font_size=44)
        anti_eq.next_to(equation, DOWN, buff=0.5)

        self.play(FadeIn(eq_label), run_time=0.5)
        self.play(Write(equation), run_time=1.5)
        self.wait(0.5)
        self.play(Write(anti_eq), run_time=1.5)
        self.wait(1)

        # Cross it out!
        cross = Cross(VGroup(equation, anti_eq), color="#CC0000", stroke_width=4)
        wrong = Text("WRONG!", color="#CC0000", font_size=48, font="sans-serif")
        wrong.next_to(anti_eq, DOWN, buff=0.8)

        self.play(Create(cross), FadeIn(wrong, scale=1.5), run_time=1)
        self.wait(2)

        # Fade all
        self.play(*[FadeOut(m) for m in self.mobjects], run_time=1)
