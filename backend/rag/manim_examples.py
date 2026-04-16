"""
Comprehensive Manim code examples for RAG retrieval.
Sourced from: Manim Community docs, 3b1b patterns, TannerGilbert examples.
These are tested, working patterns the animation agent adapts from.

GENERALIZATION RULES embedded in each example:
- Every pattern shows the PRINCIPLE, not just one use case
- Comments explain WHY each choice was made
- Variants shown for different math topics
"""

MANIM_EXAMPLES = [

    # ═══════════════════════════════════════════════════════════
    # CATEGORY 1: CORE LAYOUT & SCENE STRUCTURE
    # ═══════════════════════════════════════════════════════════

    {
        "topic": "scene_structure_template",
        "description": "Master template for any scene: title → visual → equation → caption → transition",
        "tags": ["template", "layout", "structure", "title", "transition", "any topic"],
        "code": '''
# ══ MASTER SCENE TEMPLATE ══
# Use this structure for EVERY scene. Never deviate.

# 1. Title (always YELLOW, always TOP)
title = Text("Your Scene Title", font_size=38, color=YELLOW)
title.to_edge(UP, buff=0.3)
self.play(Write(title, run_time=1.2))
self.wait(1.0)

# 2. Main visual (CONTENT zone: y = -1.8 to 2.5)
# ... build your visual here step by step ...

# 3. Equation (always at y=-2.6, always AFTER visual)
eq = safe_tex(r"your_equation_here", font_size=46)
eq.move_to([0, -2.6, 0])
self.play(Write(eq, run_time=2.0))
self.wait(2.0)  # NEVER skip this wait

# 4. Caption (plain English, GREY, y=-3.3)
cap = Text("Plain English explanation of what was just shown",
           font_size=26, color=GREY)
cap.move_to([0, -3.3, 0])
self.play(FadeIn(cap, run_time=1.0))
self.wait(1.5)

# 5. Clean transition (ALWAYS end scenes this way)
self.play(FadeOut(*self.mobjects, run_time=1.0))
self.wait(0.5)
'''
    },

    {
        "topic": "opening_hook_scene",
        "description": "3b1b-style opening hook: pose a surprising question before showing math",
        "tags": ["hook", "opener", "3b1b style", "curiosity", "any topic"],
        "code": '''
# ══ OPENING HOOK — pose a question, build curiosity ══
# From 3b1b pattern: never start with an equation, start with wonder

title = Text("A Surprising Pattern", font_size=42, color=YELLOW)
title.to_edge(UP, buff=0.3)
self.play(Write(title, run_time=1.5))
self.wait(0.8)

# Show a concrete example FIRST (e.g. a triangle, a shape, a number)
question = Text("Why does this always work?", font_size=34, color=WHITE)
question.move_to([0, 0.5, 0])
self.play(FadeIn(question, shift=UP*0.3, run_time=1.2))
self.wait(1.0)

# Add visual emphasis — hint at the mystery
hint = Text("No matter what triangle you pick...", font_size=28, color=GREY)
hint.next_to(question, DOWN, buff=0.4)
self.play(FadeIn(hint, run_time=1.0))
self.wait(2.0)

# Scene 1 never has an equation — just build curiosity
self.play(FadeOut(*self.mobjects, run_time=1.0))
self.wait(0.5)
'''
    },

    {
        "topic": "vgroup_layout",
        "description": "Use VGroup to arrange multiple objects without overlap - works for any content",
        "tags": ["layout", "vgroup", "arrange", "no overlap", "positioning"],
        "code": '''
# ══ VGROUP ARRANGEMENT — prevents overlap automatically ══
# Use VGroup.arrange() instead of manual positioning when possible

# Vertical stack (for step-by-step reveals)
steps = VGroup(
    Text("Step 1: Identify the right angle", font_size=30),
    Text("Step 2: Label the sides a, b, c", font_size=30),
    Text("Step 3: Apply the formula", font_size=30),
).arrange(DOWN, buff=0.4, aligned_edge=LEFT)
steps.move_to([0, 0.5, 0])

# Reveal one by one
for step in steps:
    self.play(FadeIn(step, shift=RIGHT*0.3, run_time=0.8))
    self.wait(0.6)
self.wait(1.0)

# Horizontal layout (for comparisons)
comparison = VGroup(
    safe_tex(r"a^2 + b^2", font_size=40, color=BLUE),
    Text("  =  ", font_size=40),
    safe_tex(r"c^2", font_size=40, color=GREEN),
).arrange(RIGHT, buff=0.2)
comparison.move_to([0, -2.6, 0])
self.play(Write(comparison, run_time=2.0))
self.wait(2.0)
'''
    },

    # ═══════════════════════════════════════════════════════════
    # CATEGORY 2: GEOMETRY DIAGRAMS
    # ═══════════════════════════════════════════════════════════

    {
        "topic": "right_triangle_complete",
        "description": "Complete right triangle with right angle marker, labeled sides, colored by role",
        "tags": ["triangle", "right angle", "geometry", "pythagorean", "labels", "sides"],
        "code": '''
# ══ RIGHT TRIANGLE — complete with all labels ══
# Positions chosen to keep triangle in CONTENT zone

A = np.array([-2.5, -1.5, 0])  # right angle vertex (bottom-left)
B = np.array([2.5, -1.5, 0])   # bottom-right
C = np.array([-2.5, 1.8, 0])   # top-left

tri = Polygon(A, B, C, color=WHITE, stroke_width=2.5)

# Right angle marker (use RightAngle, not a square manually)
right_angle = RightAngle(
    Line(A, B), Line(A, C),
    length=0.3, color=YELLOW, stroke_width=2
)

# Labels — use next_to on the LINE, not the vertex
label_a = Text("a", font_size=34, color=BLUE)
label_a.next_to(Line(A, C), LEFT, buff=0.25)

label_b = Text("b", font_size=34, color=RED)
label_b.next_to(Line(A, B), DOWN, buff=0.25)

label_c = Text("c", font_size=34, color=GREEN)
label_c.next_to(Line(B, C), RIGHT, buff=0.25)

# Animate: triangle first, then right angle, then labels
self.play(Create(tri, run_time=1.5))
self.wait(0.5)
self.play(Create(right_angle, run_time=0.8))
self.wait(0.5)
self.play(
    Write(label_a, run_time=0.8),
    Write(label_b, run_time=0.8),
    Write(label_c, run_time=0.8),
)
self.wait(1.0)
'''
    },

    {
        "topic": "squares_on_triangle_sides",
        "description": "Geometric proof of Pythagorean theorem: colored squares on each side",
        "tags": ["pythagorean", "geometric proof", "squares", "area", "visual proof"],
        "code": '''
# ══ SQUARES ON SIDES — geometric Pythagorean proof ══
# Key insight: color-code each square to match its side

A = np.array([-1.8, -1.2, 0])
B = np.array([1.8, -1.2, 0])
C = np.array([-1.8, 1.6, 0])

tri = Polygon(A, B, C, color=WHITE, stroke_width=2.5)
self.play(Create(tri, run_time=1.2))
self.wait(0.5)

# Square on leg 'a' (vertical left side) — BLUE
sq_a = Square(side_length=2.8, color=BLUE, fill_opacity=0.35, fill_color=BLUE)
sq_a.next_to(Line(A, C), LEFT, buff=0)
area_a = safe_tex(r"a^2", font_size=32, color=WHITE)
area_a.move_to(sq_a.get_center())

# Square on leg 'b' (horizontal bottom) — RED
sq_b = Square(side_length=3.6, color=RED, fill_opacity=0.35, fill_color=RED)
sq_b.next_to(Line(A, B), DOWN, buff=0)
area_b = safe_tex(r"b^2", font_size=32, color=WHITE)
area_b.move_to(sq_b.get_center())

# Reveal squares one at a time
self.play(FadeIn(sq_a, run_time=1.2))
self.play(Write(area_a, run_time=0.8))
self.wait(0.6)

self.play(FadeIn(sq_b, run_time=1.2))
self.play(Write(area_b, run_time=0.8))
self.wait(0.8)

# Show the key equation after visual
eq = safe_tex(r"a^2 + b^2 = c^2", font_size=48)
eq.move_to([0, -2.6, 0])
self.play(Write(eq, run_time=2.0))
self.wait(2.0)
'''
    },

    {
        "topic": "circle_with_parts",
        "description": "Circle showing radius, diameter, circumference with labels",
        "tags": ["circle", "radius", "diameter", "geometry", "area", "circumference"],
        "code": '''
# ══ CIRCLE ANATOMY ══
circle = Circle(radius=2.0, color=BLUE, stroke_width=2.5,
                fill_opacity=0.15, fill_color=BLUE)
circle.move_to([0, 0.3, 0])
center = Dot([0, 0.3, 0], color=WHITE, radius=0.08)

# Radius line
radius_line = Line([0, 0.3, 0], [2.0, 0.3, 0], color=YELLOW, stroke_width=2.5)
r_label = Text("r", font_size=32, color=YELLOW)
r_label.next_to(radius_line, UP, buff=0.1)

# Diameter line
diam_line = Line([-2.0, 0.3, 0], [2.0, 0.3, 0], color=RED, stroke_width=2)
diam_label = Text("d = 2r", font_size=28, color=RED)
diam_label.next_to(diam_line, DOWN, buff=0.2)

self.play(Create(circle, run_time=1.5))
self.play(FadeIn(center, run_time=0.5))
self.wait(0.5)
self.play(Create(radius_line, run_time=0.8), Write(r_label, run_time=0.8))
self.wait(0.8)

# Area equation at bottom
eq = safe_tex(r"A = \\pi r^2", font_size=48)
eq.move_to([0, -2.6, 0])
self.play(Write(eq, run_time=2.0))
self.wait(2.0)

cap = Text("Area grows with the SQUARE of radius", font_size=26, color=GREY)
cap.move_to([0, -3.3, 0])
self.play(FadeIn(cap, run_time=1.0))
self.wait(1.5)
'''
    },

    {
        "topic": "polygon_angles",
        "description": "Show interior angles of a polygon summing to a formula",
        "tags": ["polygon", "angles", "geometry", "interior angles", "sum"],
        "code": '''
# ══ POLYGON INTERIOR ANGLES ══
# General polygon — works for triangle (180), quadrilateral (360), etc.

# Triangle example
A = np.array([-2, -1.5, 0])
B = np.array([2, -1.5, 0])
C = np.array([0, 2, 0])

tri = Polygon(A, B, C, color=WHITE, stroke_width=2.5)
self.play(Create(tri, run_time=1.2))
self.wait(0.5)

# Angle arcs at each vertex
angle_A = Angle(Line(A, B), Line(A, C), radius=0.4, color=BLUE)
angle_B = Angle(Line(B, C), Line(B, A), radius=0.4, color=RED)
angle_C = Angle(Line(C, A), Line(C, B), radius=0.4, color=GREEN)

label_A = safe_tex(r"\\alpha", font_size=28, color=BLUE).next_to(angle_A, RIGHT*0.5+DOWN*0.3)
label_B = safe_tex(r"\\beta", font_size=28, color=RED).next_to(angle_B, LEFT*0.5+DOWN*0.3)
label_C = safe_tex(r"\\gamma", font_size=28, color=GREEN).next_to(angle_C, UP*0.3)

self.play(Create(angle_A), Create(angle_B), Create(angle_C), run_time=1.2)
self.play(Write(label_A), Write(label_B), Write(label_C), run_time=1.0)
self.wait(0.8)

eq = safe_tex(r"\\alpha + \\beta + \\gamma = 180°", font_size=44)
eq.move_to([0, -2.6, 0])
self.play(Write(eq, run_time=2.0))
self.wait(2.0)
'''
    },

    # ═══════════════════════════════════════════════════════════
    # CATEGORY 3: GRAPHS AND FUNCTIONS
    # ═══════════════════════════════════════════════════════════

    {
        "topic": "axes_function_plot",
        "description": "Plot any mathematical function on labeled axes - universal pattern",
        "tags": ["axes", "graph", "function", "plot", "calculus", "algebra"],
        "code": '''
# ══ FUNCTION PLOT — universal pattern for any f(x) ══
axes = Axes(
    x_range=[-3, 3, 1],
    y_range=[-2, 4, 1],
    x_length=8,
    y_length=5,
    axis_config={"color": GREY, "stroke_width": 1.5},
    tips=True,
)
axes.move_to([0, 0.2, 0])

# Axis labels
x_label = Text("x", font_size=28, color=GREY).next_to(axes.x_axis, RIGHT, buff=0.2)
y_label = Text("f(x)", font_size=28, color=GREY).next_to(axes.y_axis, UP, buff=0.2)

# Plot function (change lambda for any function)
graph = axes.plot(lambda x: x**2, color=YELLOW, stroke_width=2.5)
graph_label = safe_tex(r"f(x) = x^2", font_size=32, color=YELLOW)
graph_label.next_to(axes.c2p(2, 4), RIGHT, buff=0.1)

self.play(Create(axes, run_time=1.5))
self.play(Write(x_label), Write(y_label), run_time=0.8)
self.wait(0.5)
self.play(Create(graph, run_time=2.0))
self.play(Write(graph_label, run_time=1.0))
self.wait(1.5)

# Add equation at bottom
eq = safe_tex(r"f(x) = x^2", font_size=46)
eq.move_to([0, -2.6, 0])
self.play(Write(eq, run_time=1.5))
self.wait(2.0)
'''
    },

    {
        "topic": "derivative_tangent_line",
        "description": "Show derivative as slope of tangent line at a point - 3b1b style",
        "tags": ["derivative", "tangent", "calculus", "slope", "rate of change"],
        "code": '''
# ══ DERIVATIVE AS TANGENT LINE ══
axes = Axes(
    x_range=[-0.5, 3.5, 1], y_range=[-0.5, 5, 1],
    x_length=7, y_length=5,
    axis_config={"color": GREY}
)
axes.move_to([0, 0.2, 0])
curve = axes.plot(lambda x: x**2, color=BLUE, stroke_width=2.5)

self.play(Create(axes, run_time=1.2), Create(curve, run_time=1.5))
self.wait(0.8)

# Show tangent at x=1.5
x0 = 1.5
slope = 2 * x0  # f'(x) = 2x
y0 = x0**2

point_dot = Dot(axes.c2p(x0, y0), color=YELLOW, radius=0.12)
tangent = axes.plot(
    lambda x: slope * (x - x0) + y0,
    x_range=[x0 - 1.2, x0 + 1.2],
    color=RED, stroke_width=2.5
)

# Dashed lines showing the point
v_dash = DashedLine(axes.c2p(x0, 0), axes.c2p(x0, y0), color=GREY, stroke_width=1.5)
h_dash = DashedLine(axes.c2p(0, y0), axes.c2p(x0, y0), color=GREY, stroke_width=1.5)

self.play(Create(v_dash), Create(h_dash), run_time=0.8)
self.play(FadeIn(point_dot, run_time=0.8))
self.wait(0.5)
self.play(Create(tangent, run_time=1.2))
self.wait(0.8)

# Slope label
slope_text = safe_tex(rf"f'({x0}) = {slope}", font_size=36, color=RED)
slope_text.move_to([0, -2.6, 0])
self.play(Write(slope_text, run_time=1.5))
self.wait(2.0)

cap = Text("The derivative is the slope of the tangent line", font_size=26, color=GREY)
cap.move_to([0, -3.3, 0])
self.play(FadeIn(cap, run_time=1.0))
self.wait(1.5)
'''
    },

    {
        "topic": "area_under_curve_integral",
        "description": "Show definite integral as area under curve with shading",
        "tags": ["integral", "area", "calculus", "definite integral", "shading"],
        "code": '''
# ══ INTEGRAL AS AREA UNDER CURVE ══
axes = Axes(
    x_range=[0, 4, 1], y_range=[0, 5, 1],
    x_length=7, y_length=5,
    axis_config={"color": GREY}
)
axes.move_to([0, 0.2, 0])

curve = axes.plot(lambda x: 0.5*x**2 + 0.5, color=BLUE, stroke_width=2.5)

# Shaded area between a=1 and b=3
area = axes.get_area(curve, x_range=[1, 3], color=YELLOW, opacity=0.4)

# Boundary markers
a_line = DashedLine(axes.c2p(1, 0), axes.c2p(1, 1.0), color=RED)
b_line = DashedLine(axes.c2p(3, 0), axes.c2p(3, 5.0), color=RED)
a_label = Text("a", font_size=28, color=RED).next_to(axes.c2p(1, 0), DOWN, buff=0.2)
b_label = Text("b", font_size=28, color=RED).next_to(axes.c2p(3, 0), DOWN, buff=0.2)

self.play(Create(axes, run_time=1.2), Create(curve, run_time=1.5))
self.wait(0.5)
self.play(Create(a_line), Create(b_line), Write(a_label), Write(b_label), run_time=0.8)
self.play(FadeIn(area, run_time=1.2))
self.wait(0.8)

eq = safe_tex(r"\\int_a^b f(x)\\,dx", font_size=48)
eq.move_to([0, -2.6, 0])
self.play(Write(eq, run_time=2.0))
self.wait(2.0)

cap = Text("The integral measures the area between the curve and x-axis",
           font_size=24, color=GREY)
cap.move_to([0, -3.3, 0])
self.play(FadeIn(cap, run_time=1.0))
self.wait(1.5)
'''
    },

    {
        "topic": "number_plane_vectors",
        "description": "Show vectors on a number plane - for linear algebra topics",
        "tags": ["vector", "linear algebra", "number plane", "arrow", "transformation"],
        "code": '''
# ══ VECTORS ON NUMBER PLANE ══
plane = NumberPlane(
    x_range=[-4, 4, 1], y_range=[-3, 3, 1],
    background_line_style={"stroke_color": GREY, "stroke_width": 0.8, "stroke_opacity": 0.4}
)
self.play(Create(plane, run_time=1.5))
self.wait(0.5)

# Vector v1
v1 = Arrow(ORIGIN, [2, 1, 0], buff=0, color=YELLOW, stroke_width=3)
v1_label = safe_tex(r"\\vec{v}", font_size=32, color=YELLOW)
v1_label.next_to(v1.get_end(), UR, buff=0.15)

# Vector v2
v2 = Arrow(ORIGIN, [1, 2, 0], buff=0, color=RED, stroke_width=3)
v2_label = safe_tex(r"\\vec{u}", font_size=32, color=RED)
v2_label.next_to(v2.get_end(), UL, buff=0.15)

# Sum vector (parallelogram law)
v_sum = Arrow(ORIGIN, [3, 3, 0], buff=0, color=GREEN, stroke_width=3)
sum_label = safe_tex(r"\\vec{v}+\\vec{u}", font_size=28, color=GREEN)
sum_label.next_to(v_sum.get_end(), RIGHT, buff=0.15)

self.play(Create(v1), Write(v1_label), run_time=1.0)
self.play(Create(v2), Write(v2_label), run_time=1.0)
self.wait(0.5)
self.play(Create(v_sum), Write(sum_label), run_time=1.2)
self.wait(1.5)
'''
    },

    {
        "topic": "sine_cosine_unit_circle",
        "description": "Unit circle showing sin and cos as coordinates - 3b1b style",
        "tags": ["trig", "sine", "cosine", "unit circle", "trigonometry", "angle"],
        "code": '''
# ══ UNIT CIRCLE — sin and cos as coordinates ══
axes = Axes(
    x_range=[-1.5, 1.5, 0.5], y_range=[-1.5, 1.5, 0.5],
    x_length=5, y_length=5,
    axis_config={"color": GREY}
)
axes.move_to([-1.5, 0.3, 0])

circle = Circle(radius=2.5, color=WHITE, stroke_width=2)
circle.move_to([-1.5, 0.3, 0])

# Angle theta
theta = PI / 4  # 45 degrees
px = np.cos(theta)
py = np.sin(theta)

# Point on circle (scaled to display)
scale = 2.5
point = axes.c2p(px, py)
dot = Dot(point, color=YELLOW, radius=0.12)

# Radius line
radius = Line(axes.c2p(0, 0), point, color=YELLOW, stroke_width=2.5)

# Projection lines
cos_line = DashedLine(axes.c2p(0, 0), axes.c2p(px, 0), color=RED, stroke_width=2)
sin_line = DashedLine(axes.c2p(px, 0), axes.c2p(px, py), color=BLUE, stroke_width=2)

cos_label = Text("cos θ", font_size=26, color=RED).next_to(axes.c2p(px/2, 0), DOWN, buff=0.2)
sin_label = Text("sin θ", font_size=26, color=BLUE).next_to(axes.c2p(px, py/2), RIGHT, buff=0.2)

# Angle arc
angle_arc = Arc(radius=0.4, start_angle=0, angle=theta, color=GREEN)
angle_arc.move_arc_center_to(axes.c2p(0, 0))
theta_label = safe_tex(r"\\theta", font_size=28, color=GREEN)
theta_label.next_to(angle_arc, RIGHT, buff=0.1)

self.play(Create(axes, run_time=1.0), Create(circle, run_time=1.5))
self.play(Create(radius), FadeIn(dot), run_time=0.8)
self.play(Create(angle_arc), Write(theta_label), run_time=0.8)
self.play(Create(cos_line), Create(sin_line), run_time=1.0)
self.play(Write(cos_label), Write(sin_label), run_time=0.8)
self.wait(1.0)

eq = safe_tex(r"\\sin^2\\theta + \\cos^2\\theta = 1", font_size=44)
eq.move_to([2.5, -2.6, 0])
self.play(Write(eq, run_time=2.0))
self.wait(2.0)
'''
    },

    # ═══════════════════════════════════════════════════════════
    # CATEGORY 4: EQUATION ANIMATIONS
    # ═══════════════════════════════════════════════════════════

    {
        "topic": "equation_step_by_step",
        "description": "Transform equation step by step - show algebraic manipulation",
        "tags": ["algebra", "equation", "transform", "step by step", "manipulation"],
        "code": '''
# ══ STEP-BY-STEP EQUATION TRANSFORM ══
# Pattern: show each algebraic step as a Transform
# Works for any algebraic manipulation

title = Text("Solving Step by Step", font_size=38, color=YELLOW)
title.to_edge(UP, buff=0.3)
self.play(Write(title, run_time=1.2))
self.wait(0.8)

# Step 1: Start
step1 = safe_tex(r"a^2 + b^2 = c^2", font_size=52)
step1.move_to([0, 0.5, 0])
label1 = Text("Start with:", font_size=28, color=GREY)
label1.next_to(step1, UP, buff=0.3)
self.play(FadeIn(label1), Write(step1, run_time=1.5))
self.wait(1.5)

# Step 2: Rearrange
step2 = safe_tex(r"c^2 = a^2 + b^2", font_size=52)
step2.move_to([0, 0.5, 0])
self.play(Transform(step1, step2, run_time=1.2))
self.wait(1.2)

# Step 3: Solve for c
step3 = safe_tex(r"c = \\sqrt{a^2 + b^2}", font_size=52)
step3.move_to([0, 0.5, 0])
self.play(Transform(step1, step3, run_time=1.2))
self.wait(1.5)

cap = Text("We isolated c — the hypotenuse length", font_size=26, color=GREY)
cap.move_to([0, -3.3, 0])
self.play(FadeIn(cap, run_time=1.0))
self.wait(1.5)
'''
    },

    {
        "topic": "worked_example_numbers",
        "description": "Plug in numbers and compute step by step - 3-4-5 or any triple",
        "tags": ["worked example", "numbers", "arithmetic", "verification", "pythagorean"],
        "code": '''
# ══ WORKED NUMERICAL EXAMPLE ══
# Pattern: show the computation step by step with Transforms

title = Text("Let's check: 3-4-5 triangle", font_size=38, color=YELLOW)
title.to_edge(UP, buff=0.3)
self.play(Write(title, run_time=1.2))
self.wait(0.8)

# Draw the triangle with numbers
A = np.array([-2.0, -1.5, 0])
B = np.array([2.0, -1.5, 0])
C = np.array([-2.0, 1.5, 0])
tri = Polygon(A, B, C, color=WHITE, stroke_width=2.5)
n3 = Text("3", font_size=34, color=BLUE).next_to(Line(A, C), LEFT, buff=0.25)
n4 = Text("4", font_size=34, color=RED).next_to(Line(A, B), DOWN, buff=0.25)
n5 = Text("5", font_size=34, color=GREEN).next_to(Line(B, C), RIGHT, buff=0.25)
right_angle = RightAngle(Line(A, B), Line(A, C), length=0.25, color=YELLOW)

self.play(Create(tri, run_time=1.2), Create(right_angle, run_time=0.6))
self.play(Write(n3), Write(n4), Write(n5), run_time=1.0)
self.wait(0.8)

# Computation steps
s1 = safe_tex(r"3^2 + 4^2", font_size=46).move_to([3.2, 0.5, 0])
self.play(Write(s1, run_time=1.2)); self.wait(1.0)

s2 = safe_tex(r"9 + 16", font_size=46).move_to([3.2, 0.5, 0])
self.play(Transform(s1, s2, run_time=1.0)); self.wait(1.0)

s3 = safe_tex(r"= 25", font_size=46).move_to([3.2, 0.5, 0])
self.play(Transform(s1, s3, run_time=1.0)); self.wait(0.8)

s4 = safe_tex(r"= 5^2 \\checkmark", font_size=46, color=GREEN).move_to([3.2, 0.5, 0])
self.play(Transform(s1, s4, run_time=1.0)); self.wait(1.5)

eq = safe_tex(r"a^2 + b^2 = c^2", font_size=46)
eq.move_to([0, -2.6, 0])
self.play(Write(eq, run_time=1.5)); self.wait(2.0)
'''
    },

    {
        "topic": "equation_highlight_parts",
        "description": "Highlight specific terms in an equation by color - focus attention",
        "tags": ["equation", "highlight", "color", "emphasis", "algebra", "any equation"],
        "code": '''
# ══ EQUATION PART HIGHLIGHTING ══
# Pattern: write full equation, then highlight parts with color transforms

eq = safe_tex(r"a^2 + b^2 = c^2", font_size=56)
eq.move_to([0, 0.5, 0])
self.play(Write(eq, run_time=2.0))
self.wait(1.0)

# Highlight 'a^2' in BLUE
eq_colored = safe_tex(r"a^2 + b^2 = c^2", font_size=56)
eq_colored.move_to([0, 0.5, 0])
# Color individual parts
eq_colored[0][0:2].set_color(BLUE)   # a^2
eq_colored[0][3:5].set_color(RED)    # b^2
eq_colored[0][6:8].set_color(GREEN)  # c^2
self.play(Transform(eq, eq_colored, run_time=1.2))
self.wait(1.0)

# Explain each color
labels = VGroup(
    Text("leg a", font_size=26, color=BLUE),
    Text("leg b", font_size=26, color=RED),
    Text("hypotenuse c", font_size=26, color=GREEN),
).arrange(RIGHT, buff=0.8)
labels.move_to([0, -1.5, 0])
self.play(FadeIn(labels, run_time=1.2))
self.wait(1.5)
'''
    },

    # ═══════════════════════════════════════════════════════════
    # CATEGORY 5: TRANSFORMATIONS & ANIMATIONS
    # ═══════════════════════════════════════════════════════════

    {
        "topic": "shape_transform",
        "description": "Smoothly transform one shape into another - from official docs",
        "tags": ["transform", "morphing", "shape", "animation", "transition"],
        "code": '''
# ══ SHAPE TRANSFORMATION ══
# From official Manim docs: SquareToCircle pattern

square = Square(color=BLUE, fill_opacity=0.4, fill_color=BLUE)
square.move_to([0, 0.3, 0])
square_label = Text("Square", font_size=28, color=GREY)
square_label.next_to(square, DOWN, buff=0.3)

self.play(Create(square, run_time=1.2))
self.play(Write(square_label, run_time=0.8))
self.wait(0.8)

circle = Circle(color=RED, fill_opacity=0.4, fill_color=RED)
circle.move_to([0, 0.3, 0])
circle_label = Text("Circle", font_size=28, color=GREY)
circle_label.next_to(circle, DOWN, buff=0.3)

# The magic: Transform smoothly interpolates
self.play(
    Transform(square, circle, run_time=1.5),
    Transform(square_label, circle_label, run_time=1.5)
)
self.wait(1.5)

# ReplacementTransform for cleaner variable management
# Use when you want the new object to fully replace the old
'''
    },

    {
        "topic": "dot_moving_on_path",
        "description": "Animate a point moving along a curve or path",
        "tags": ["moving point", "path", "parametric", "animation", "tracing"],
        "code": '''
# ══ POINT MOVING ALONG PATH ══
# From official Manim docs: MoveAlongPath

axes = Axes(x_range=[-3, 3, 1], y_range=[-2, 2, 1], x_length=8, y_length=5)
axes.move_to([0, 0.2, 0])
curve = axes.plot(lambda x: np.sin(x), color=BLUE, stroke_width=2.5)

# Moving dot traces the curve
moving_dot = Dot(color=YELLOW, radius=0.12)
moving_dot.move_to(axes.c2p(-3, np.sin(-3)))

# Trace path (ValueTracker approach)
trace = VMobject(color=RED, stroke_width=3)
trace.set_points_as_corners([moving_dot.get_center()])

def update_trace(mob):
    mob.add_points_as_corners([moving_dot.get_center()])

trace.add_updater(update_trace)

self.play(Create(axes, run_time=1.2), Create(curve, run_time=1.5))
self.add(moving_dot, trace)
self.wait(0.5)
self.play(MoveAlongPath(moving_dot, curve, run_time=4, rate_func=linear))
trace.remove_updater(update_trace)
self.wait(1.5)
'''
    },

    {
        "topic": "brace_annotation",
        "description": "Use Brace to annotate distances or lengths - from official examples",
        "tags": ["brace", "annotation", "label", "distance", "geometry", "measurement"],
        "code": '''
# ══ BRACE ANNOTATION ══
# From official Manim Community examples

# Annotate horizontal distance
dot1 = Dot([-2, -1, 0], color=WHITE)
dot2 = Dot([2, 1, 0], color=WHITE)
line = Line(dot1.get_center(), dot2.get_center(), color=ORANGE, stroke_width=2.5)

# Horizontal brace (below)
brace_h = Brace(line, direction=DOWN)
brace_h_text = brace_h.get_text("Horizontal distance")

# Vertical brace (perpendicular to line)
brace_v = Brace(line, direction=line.copy().rotate(PI/2).get_unit_vector())
brace_v_tex = brace_v.get_tex(r"\\Delta y")

self.play(Create(line), FadeIn(dot1), FadeIn(dot2), run_time=1.0)
self.play(Create(brace_h), Write(brace_h_text), run_time=1.2)
self.wait(0.8)
self.play(Create(brace_v), Write(brace_v_tex), run_time=1.2)
self.wait(1.5)

# Brace for equations too
eq = safe_tex(r"a^2 + b^2 = c^2", font_size=48).move_to([0, -1.0, 0])
eq_brace = Brace(eq, direction=DOWN)
eq_brace_text = eq_brace.get_text("Pythagorean Theorem")
self.play(Write(eq, run_time=1.5))
self.play(Create(eq_brace), Write(eq_brace_text), run_time=1.2)
self.wait(1.5)
'''
    },

    {
        "topic": "number_line_visualization",
        "description": "Number line for showing values, inequalities, limits approaching",
        "tags": ["number line", "real numbers", "limit", "inequality", "approaching"],
        "code": '''
# ══ NUMBER LINE ══
nl = NumberLine(
    x_range=[-4, 4, 1],
    length=10,
    include_numbers=True,
    include_tip=True,
    numbers_with_elongated_ticks=[0],
)
nl.move_to([0, 0, 0])
self.play(Create(nl, run_time=1.5))
self.wait(0.5)

# Mark a specific value
val = 2.5
dot = Dot(nl.n2p(val), color=YELLOW, radius=0.15)
val_label = safe_tex(rf"{val}", font_size=30, color=YELLOW)
val_label.next_to(dot, UP, buff=0.2)
self.play(FadeIn(dot), Write(val_label), run_time=0.8)
self.wait(0.8)

# Show two values approaching each other (limit intuition)
left_dot = Dot(nl.n2p(-3), color=RED, radius=0.12)
right_dot = Dot(nl.n2p(3), color=BLUE, radius=0.12)
self.play(FadeIn(left_dot), FadeIn(right_dot), run_time=0.8)

# Move toward center
self.play(
    left_dot.animate.move_to(nl.n2p(0)),
    right_dot.animate.move_to(nl.n2p(0)),
    run_time=2.0, rate_func=smooth
)
self.wait(1.0)
'''
    },

    # ═══════════════════════════════════════════════════════════
    # CATEGORY 6: LINEAR ALGEBRA
    # ═══════════════════════════════════════════════════════════

    {
        "topic": "matrix_display",
        "description": "Display matrix and compute determinant or show multiplication",
        "tags": ["matrix", "linear algebra", "determinant", "2x2", "3x3"],
        "code": '''
# ══ MATRIX DISPLAY ══
title = Text("Matrix Operations", font_size=38, color=YELLOW)
title.to_edge(UP, buff=0.3)
self.play(Write(title, run_time=1.2))
self.wait(0.8)

# 2x2 matrix
mat = Matrix(
    [["a", "b"], ["c", "d"]],
    element_to_mobject_config={"font_size": 40}
)
mat.move_to([-2.5, 0.3, 0])
self.play(Write(mat, run_time=1.5))
self.wait(0.8)

# Determinant label
arrow = Arrow(mat.get_right(), [0, 0.3, 0], buff=0.2, color=YELLOW)
det = VGroup(
    Text("det = ", font_size=34),
    safe_tex(r"ad - bc", font_size=40)
).arrange(RIGHT, buff=0.1).move_to([2.5, 0.3, 0])

self.play(Create(arrow, run_time=0.8))
self.play(Write(det, run_time=1.5))
self.wait(0.8)

eq = safe_tex(r"\\det(A) = ad - bc", font_size=44)
eq.move_to([0, -2.6, 0])
self.play(Write(eq, run_time=2.0))
self.wait(2.0)
'''
    },

    {
        "topic": "linear_transformation_grid",
        "description": "Show linear transformation applied to a grid - 3b1b signature style",
        "tags": ["linear algebra", "transformation", "grid", "matrix", "eigenvector", "3b1b"],
        "code": '''
# ══ LINEAR TRANSFORMATION ON GRID ══
# 3b1b signature: show how matrix transforms the plane

# Create background grid
grid = NumberPlane(
    background_line_style={"stroke_color": BLUE, "stroke_opacity": 0.3}
)
basis_i = Arrow(ORIGIN, [1, 0, 0], buff=0, color=GREEN, stroke_width=4)
basis_j = Arrow(ORIGIN, [0, 1, 0], buff=0, color=RED, stroke_width=4)
i_label = Text("i", font_size=28, color=GREEN).next_to(basis_i.get_end(), DOWN)
j_label = Text("j", font_size=28, color=RED).next_to(basis_j.get_end(), LEFT)

self.play(Create(grid, run_time=2.0))
self.play(Create(basis_i), Create(basis_j),
          Write(i_label), Write(j_label), run_time=1.0)
self.wait(0.8)

# Apply 2x2 matrix transformation [[2,1],[1,2]]
matrix = [[2, 1], [1, 2]]
self.play(
    grid.animate.apply_matrix(matrix),
    basis_i.animate.put_start_and_end_on(ORIGIN, [2, 1, 0]),
    basis_j.animate.put_start_and_end_on(ORIGIN, [1, 2, 0]),
    run_time=2.5, rate_func=smooth
)
self.wait(1.5)

eq = safe_tex(r"\\begin{pmatrix}2&1\\\\1&2\\end{pmatrix}", font_size=44)
eq.move_to([0, -2.6, 0])
self.play(Write(eq, run_time=1.5))
self.wait(2.0)
'''
    },

    # ═══════════════════════════════════════════════════════════
    # CATEGORY 7: PROBABILITY & STATISTICS
    # ═══════════════════════════════════════════════════════════

    {
        "topic": "bar_chart_probability",
        "description": "Bar chart showing probability distribution",
        "tags": ["probability", "statistics", "bar chart", "distribution", "histogram"],
        "code": '''
# ══ PROBABILITY BAR CHART ══
chart = BarChart(
    values=[0.1, 0.15, 0.25, 0.25, 0.15, 0.1],
    bar_names=["1", "2", "3", "4", "5", "6"],
    y_range=[0, 0.3, 0.1],
    y_length=4,
    x_length=8,
    bar_colors=[BLUE, BLUE, BLUE, BLUE, BLUE, BLUE],
    bar_fill_opacity=0.7,
)
chart.move_to([0, 0.3, 0])

x_label = Text("Outcome", font_size=28, color=GREY)
x_label.next_to(chart, DOWN, buff=0.5)
y_label = Text("P(X=k)", font_size=28, color=GREY)
y_label.next_to(chart, LEFT, buff=0.3)

self.play(Create(chart, run_time=2.0))
self.play(Write(x_label), Write(y_label), run_time=0.8)
self.wait(1.0)

cap = Text("Each bar shows the probability of that outcome", font_size=26, color=GREY)
cap.move_to([0, -3.3, 0])
self.play(FadeIn(cap, run_time=1.0))
self.wait(1.5)
'''
    },

    # ═══════════════════════════════════════════════════════════
    # CATEGORY 8: GENERALIZATION PATTERNS
    # ═══════════════════════════════════════════════════════════

    {
        "topic": "general_proof_structure",
        "description": "Universal pattern for showing any mathematical proof visually",
        "tags": ["proof", "general", "theorem", "logic", "any topic", "structure"],
        "code": '''
# ══ PROOF STRUCTURE — works for ANY theorem ══
# Pattern: Claim → Visual Evidence → Formal Statement

# 1. State the claim
claim = Text("Claim: [state theorem here]", font_size=32, color=YELLOW)
claim.move_to([0, 2.0, 0])
self.play(Write(claim, run_time=1.5))
self.wait(1.0)

# 2. Show visual evidence (specific case first)
evidence_label = Text("Evidence (specific case):", font_size=28, color=GREY)
evidence_label.move_to([0, 0.8, 0])
self.play(FadeIn(evidence_label, run_time=0.8))

# ... draw your specific example here ...
specific = Text("[visual example goes here]", font_size=26)
specific.move_to([0, 0.0, 0])
self.play(FadeIn(specific, run_time=1.0))
self.wait(1.2)

# 3. Generalize
general_label = Text("For ALL cases:", font_size=28, color=WHITE)
general_label.move_to([0, -1.2, 0])
self.play(Write(general_label, run_time=0.8))
self.wait(0.5)

# 4. Formal equation
eq = safe_tex(r"[formal statement here]", font_size=44)
eq.move_to([0, -2.6, 0])
self.play(Write(eq, run_time=2.0))
self.wait(2.0)
'''
    },

    {
        "topic": "side_by_side_comparison",
        "description": "Show two concepts side by side for comparison - universal layout",
        "tags": ["comparison", "side by side", "contrast", "two cases", "any topic"],
        "code": '''
# ══ SIDE-BY-SIDE COMPARISON ══
# Universal: compare two cases, two formulas, two shapes

# Left panel
left_box = Rectangle(width=5.5, height=4.5, color=BLUE, stroke_width=1.5)
left_box.move_to([-3.2, 0.3, 0])
left_title = Text("Case A", font_size=30, color=BLUE)
left_title.next_to(left_box, UP, buff=0.1)

# Right panel
right_box = Rectangle(width=5.5, height=4.5, color=RED, stroke_width=1.5)
right_box.move_to([3.2, 0.3, 0])
right_title = Text("Case B", font_size=30, color=RED)
right_title.next_to(right_box, UP, buff=0.1)

# Divider
divider = DashedLine([0, 2.5, 0], [0, -2.0, 0], color=GREY, stroke_width=1)

self.play(
    Create(left_box), Create(right_box),
    Write(left_title), Write(right_title),
    Create(divider), run_time=1.2
)
self.wait(0.5)

# Add content to each panel
left_content = safe_tex(r"a^2 + b^2 = c^2", font_size=36)
left_content.move_to([-3.2, 0.3, 0])
right_content = safe_tex(r"a^2 + b^2 \\neq c^2", font_size=36)
right_content.move_to([3.2, 0.3, 0])

self.play(Write(left_content), Write(right_content), run_time=1.5)
self.wait(1.5)

# Conclusion
conclusion = Text("The equation determines the triangle type",
                  font_size=26, color=GREY)
conclusion.move_to([0, -3.3, 0])
self.play(FadeIn(conclusion, run_time=1.0))
self.wait(1.5)
'''
    },

    {
        "topic": "updater_dynamic_label",
        "description": "Dynamic label that updates as a value changes - ValueTracker pattern",
        "tags": ["updater", "dynamic", "value tracker", "animation", "changing value"],
        "code": '''
# ══ DYNAMIC UPDATING LABEL ══
# ValueTracker: animate a changing quantity with live label

axes = Axes(x_range=[-3, 3, 1], y_range=[-2, 4, 1], x_length=7, y_length=5)
axes.move_to([0, 0.2, 0])
self.play(Create(axes, run_time=1.2))

# ValueTracker controls the x position
x_tracker = ValueTracker(0)

# Moving dot
dot = always_redraw(lambda:
    Dot(axes.c2p(x_tracker.get_value(),
                 x_tracker.get_value()**2),
        color=YELLOW, radius=0.12)
)

# Dynamic label showing current coordinates
coord_label = always_redraw(lambda:
    Text(f"x = {x_tracker.get_value():.1f}",
         font_size=28, color=YELLOW
    ).next_to(dot, UR, buff=0.15)
)

curve = axes.plot(lambda x: x**2, color=BLUE, stroke_width=2.5)
self.play(Create(curve, run_time=1.5))
self.add(dot, coord_label)
self.wait(0.5)

# Animate x from -2 to 2
self.play(x_tracker.animate.set_value(2.5), run_time=3.0, rate_func=smooth)
self.wait(0.5)
self.play(x_tracker.animate.set_value(-2.5), run_time=3.0, rate_func=smooth)
self.wait(1.0)
'''
    },

    {
        "topic": "successive_approximation",
        "description": "Show iterative refinement - for limits, Riemann sums, Taylor series",
        "tags": ["approximation", "limit", "Riemann sum", "iteration", "convergence"],
        "code": '''
# ══ SUCCESSIVE APPROXIMATION — Riemann Sums ══
# Pattern works for: Riemann sums, Taylor approximation, Newton's method

axes = Axes(
    x_range=[0, 3, 1], y_range=[0, 5, 1],
    x_length=7, y_length=5,
    axis_config={"color": GREY}
)
axes.move_to([0, 0.2, 0])
f = lambda x: x**2 + 0.5
curve = axes.plot(f, color=BLUE, stroke_width=2.5)

self.play(Create(axes, run_time=1.2), Create(curve, run_time=1.5))
self.wait(0.5)

# Show Riemann rectangles with increasing n
for n, color in [(4, RED), (8, ORANGE), (16, GREEN)]:
    rects = axes.get_riemann_rectangles(
        curve, x_range=[0, 3], dx=3/n,
        color=color, fill_opacity=0.4, stroke_width=0.8
    )
    label = Text(f"n = {n} rectangles", font_size=28, color=color)
    label.move_to([3.5, 1.5, 0])
    self.play(FadeIn(rects, run_time=0.8), Write(label, run_time=0.8))
    self.wait(1.0)
    self.play(FadeOut(rects), FadeOut(label), run_time=0.5)

eq = safe_tex(r"\\int_0^3 f(x)\\,dx = \\lim_{n\\to\\infty} \\sum_{i=1}^n f(x_i)\\Delta x",
              font_size=36)
eq.move_to([0, -2.6, 0])
self.play(Write(eq, run_time=2.0))
self.wait(2.0)
'''
    },

    {
        "topic": "boolean_set_operations",
        "description": "Show set union, intersection, complement with Venn diagrams",
        "tags": ["sets", "union", "intersection", "venn diagram", "probability", "logic"],
        "code": '''
# ══ VENN DIAGRAM — SET OPERATIONS ══
# From official Manim Community BooleanOperations example

ellipse_A = Ellipse(width=4.0, height=3.5, fill_opacity=0.5,
                    color=BLUE, stroke_width=2).move_to([-1.2, 0.3, 0])
ellipse_B = Ellipse(width=4.0, height=3.5, fill_opacity=0.5,
                    color=RED, stroke_width=2).move_to([1.2, 0.3, 0])

label_A = Text("A", font_size=36, color=WHITE).move_to([-2.2, 0.3, 0])
label_B = Text("B", font_size=36, color=WHITE).move_to([2.2, 0.3, 0])

self.play(FadeIn(ellipse_A), FadeIn(ellipse_B), run_time=1.2)
self.play(Write(label_A), Write(label_B), run_time=0.8)
self.wait(0.8)

# Highlight intersection
intersection = Intersection(ellipse_A, ellipse_B, color=YELLOW, fill_opacity=0.8)
intersection_label = Text("A ∩ B", font_size=28, color=YELLOW)
intersection_label.move_to([0, -1.8, 0])

self.play(FadeIn(intersection, run_time=1.0), Write(intersection_label, run_time=0.8))
self.wait(1.5)

eq = safe_tex(r"P(A \\cap B) = P(A) \\cdot P(B)", font_size=40)
eq.move_to([0, -2.6, 0])
self.play(Write(eq, run_time=2.0))
self.wait(2.0)
'''
    },

    {
        "topic": "fourier_series_buildup",
        "description": "Build up Fourier series term by term showing convergence",
        "tags": ["fourier", "series", "convergence", "sine", "approximation", "analysis"],
        "code": '''
# ══ FOURIER SERIES BUILDUP ══
axes = Axes(
    x_range=[-PI, PI, PI/2], y_range=[-1.5, 1.5, 0.5],
    x_length=10, y_length=4,
    axis_config={"color": GREY}
)
axes.move_to([0, 0.5, 0])
self.play(Create(axes, run_time=1.2))

# Add sine terms one by one (square wave approximation)
colors = [BLUE, RED, GREEN, YELLOW]
graphs = []
for i, (n, color) in enumerate(zip([1, 3, 5, 7], colors)):
    # Partial sum up to term n
    def make_partial(N):
        def f(x):
            return sum(
                (4 / (k * PI)) * np.sin(k * x)
                for k in range(1, N + 1, 2)
            )
        return f

    g = axes.plot(make_partial(n), color=color, stroke_width=2.0)
    label = safe_tex(rf"N={n}", font_size=28, color=color)
    label.move_to([4.5, 1.5 - i*0.5, 0])

    if graphs:
        self.play(ReplacementTransform(graphs[-1], g, run_time=1.0),
                  Write(label, run_time=0.6))
    else:
        self.play(Create(g, run_time=1.2), Write(label, run_time=0.6))
    graphs.append(g)
    self.wait(0.8)

eq = safe_tex(r"f(x) = \\sum_{n=1,3,5}^{\\infty} \\frac{4}{n\\pi} \\sin(nx)",
              font_size=36)
eq.move_to([0, -2.6, 0])
self.play(Write(eq, run_time=2.0))
self.wait(2.0)
'''
    },

    {
        "topic": "complex_number_plane",
        "description": "Show complex numbers on Argand plane with modulus and argument",
        "tags": ["complex numbers", "argand plane", "modulus", "argument", "euler"],
        "code": '''
# ══ COMPLEX NUMBER PLANE ══
plane = ComplexPlane(
    x_range=[-3, 3, 1], y_range=[-2, 2, 1],
    background_line_style={"stroke_opacity": 0.3}
)
re_label = Text("Re", font_size=26, color=GREY).next_to(plane.x_axis, RIGHT, buff=0.2)
im_label = Text("Im", font_size=26, color=GREY).next_to(plane.y_axis, UP, buff=0.2)

self.play(Create(plane, run_time=1.5))
self.play(Write(re_label), Write(im_label), run_time=0.8)
self.wait(0.5)

# Show complex number z = 2 + 1.5i
z = complex(2, 1.5)
point = plane.n2p(z)
dot = Dot(point, color=YELLOW, radius=0.12)
z_label = safe_tex(r"z = 2 + 1.5i", font_size=32, color=YELLOW)
z_label.next_to(dot, UR, buff=0.15)

# Modulus line
modulus_line = Line(plane.n2p(0), point, color=YELLOW, stroke_width=2.5)

# Real and imaginary components
re_line = DashedLine(plane.n2p(0), plane.n2p(2), color=RED, stroke_width=2)
im_line = DashedLine(plane.n2p(2), point, color=BLUE, stroke_width=2)

self.play(Create(modulus_line), FadeIn(dot), Write(z_label), run_time=1.2)
self.play(Create(re_line), Create(im_line), run_time=0.8)
self.wait(0.8)

eq = safe_tex(r"|z| = \\sqrt{a^2 + b^2}", font_size=44)
eq.move_to([0, -2.6, 0])
self.play(Write(eq, run_time=2.0))
self.wait(2.0)
'''
    },

    {
        "topic": "sequence_convergence",
        "description": "Visualize a sequence converging to a limit on a number line or graph",
        "tags": ["sequence", "convergence", "limit", "series", "epsilon delta"],
        "code": '''
# ══ SEQUENCE CONVERGENCE ══
axes = Axes(
    x_range=[0, 15, 1], y_range=[0, 2.5, 0.5],
    x_length=9, y_length=5,
    axis_config={"color": GREY}
)
axes.move_to([0, 0.2, 0])
x_label = Text("n", font_size=28, color=GREY).next_to(axes.x_axis, RIGHT)
y_label = Text("a_n", font_size=28, color=GREY).next_to(axes.y_axis, UP)

# Sequence a_n = 1 + 1/n
dots = VGroup(*[
    Dot(axes.c2p(n, 1 + 1/n), color=YELLOW, radius=0.1)
    for n in range(1, 15)
])

# Limit line
limit_line = DashedLine(axes.c2p(0, 1), axes.c2p(14, 1), color=RED, stroke_width=2)
limit_label = Text("L = 1", font_size=28, color=RED)
limit_label.next_to(axes.c2p(14, 1), RIGHT, buff=0.2)

self.play(Create(axes, run_time=1.2))
self.play(Write(x_label), Write(y_label), run_time=0.6)
self.play(Create(limit_line), Write(limit_label), run_time=1.0)
self.wait(0.5)

# Reveal dots one by one (first few), then all at once
for dot in dots[:5]:
    self.play(FadeIn(dot, run_time=0.3))
self.play(FadeIn(VGroup(*dots[5:]), run_time=1.0))
self.wait(1.0)

eq = safe_tex(r"\\lim_{n \\to \\infty} \\left(1 + \\frac{1}{n}\\right) = 1", font_size=44)
eq.move_to([0, -2.6, 0])
self.play(Write(eq, run_time=2.0))
self.wait(2.0)
'''
    },

    {
        "topic": "gradient_descent_visualization",
        "description": "Show optimization and gradient descent on a curve",
        "tags": ["optimization", "gradient descent", "minimum", "calculus", "ML"],
        "code": '''
# ══ GRADIENT DESCENT — find minimum visually ══
axes = Axes(
    x_range=[-3, 3, 1], y_range=[-1, 5, 1],
    x_length=8, y_length=5,
    axis_config={"color": GREY}
)
axes.move_to([0, 0.2, 0])
f = lambda x: x**2 + 0.5
curve = axes.plot(f, color=BLUE, stroke_width=2.5)
min_dot = Dot(axes.c2p(0, 0.5), color=GREEN, radius=0.12)
min_label = Text("minimum", font_size=26, color=GREEN)
min_label.next_to(min_dot, DOWN, buff=0.2)

self.play(Create(axes, run_time=1.2), Create(curve, run_time=1.5))
self.wait(0.5)

# Show descent: start at x=2.5, move toward minimum
x_tracker = ValueTracker(2.5)
moving_dot = always_redraw(lambda:
    Dot(axes.c2p(x_tracker.get_value(), f(x_tracker.get_value())),
        color=RED, radius=0.12)
)

self.add(moving_dot)
self.play(x_tracker.animate.set_value(0), run_time=3.0, rate_func=smooth)
self.play(FadeIn(min_dot), Write(min_label), run_time=0.8)
self.wait(1.0)

eq = safe_tex(r"\\frac{d}{dx}f(x) = 0", font_size=46)
eq.move_to([0, -2.6, 0])
self.play(Write(eq, run_time=1.5))
self.wait(2.0)
cap = Text("At minimum, the derivative equals zero", font_size=26, color=GREY)
cap.move_to([0, -3.3, 0])
self.play(FadeIn(cap, run_time=1.0))
self.wait(1.5)
'''
    },
]


# Generalization hints — injected with every retrieval
GENERALIZATION_RULES = """
GENERALIZATION PRINCIPLES FOR ANIMATION CODE:
1. ADAPT coordinates to your specific shapes — never paste coords blindly
2. SCALE font sizes: titles=38, equations=44-52, labels=28-34, captions=24-26
3. COLOR CONSISTENCY: BLUE=first concept, RED=second, GREEN=result/answer, YELLOW=highlight/title
4. POSITION CHECK: after placing every object, verify it's in the correct zone:
   - y > 2.5: too high (title zone only)
   - y = -1.8 to 2.5: content zone (shapes, graphs)
   - y = -2.6: equation zone
   - y = -3.3: caption zone
5. WAIT TIMES are non-negotiable: after equations=2.0, after shapes=0.8, after titles=1.0
6. EVERY scene ends with: self.play(FadeOut(*self.mobjects, run_time=1.0)); self.wait(0.5)
7. USE safe_tex() not MathTex() — always
8. AVOID: \\text{} in safe_tex, more than 4 objects at once, 2D coordinates
"""