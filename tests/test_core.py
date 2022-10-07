import flask
from jembewf import (
    JembeWF,
    Flow,
    FlowCallback,
    Task,
    TaskCallback,
    Transition,
    TransitionCallback,
    get_jembewf,
)


def test_extension_initialisation():
    """Ensure JembeWF is loaded into Flask"""
    jwf = JembeWF()
    app = flask.Flask(__name__)
    jwf.init_app(app)

    with app.test_request_context():
        assert jwf == get_jembewf()


def test_simple_flow_definition():
    """Test defining and running simple linear flow with three tasks"""
    jwf = JembeWF()

    jwf.add(
        Flow("flow1")
        .add(
            Task("task1").add(
                Transition("task2"),
            ),
            Task("task2").add(
                Transition("task3"),
            ),
            Task("task3"),
        )
        .start_with("task1")
    )

    # init flask app
    app = flask.Flask(__name__)
    jwf.init_app(app)

    with app.test_request_context():
        assert jwf == get_jembewf()


def test_demo_flow_definition():
    """Test defining and running demo flow"""
    jwf = JembeWF()

    class Flow1Callback(FlowCallback):
        """Flow1 Callback"""

    class Task1Callback(TaskCallback):
        """Task1 Callback"""

    class Task2Callback(TaskCallback):
        """Task 2 Callback"""

    class Task3Callback(TaskCallback):
        """Task Callback"""

    class Task4Callback(TaskCallback):
        """Task Callback"""

    class TaskEndCallback(TaskCallback):
        """Task Callback"""

    class ToTask2Callback(TransitionCallback):
        """ToTask2 Callback"""

    class ToTask3Callback(TransitionCallback):
        """Transition Callback"""

    class ToTask4Callback(TransitionCallback):
        """Transition Callback"""

    class FromTask2ToTaskEndCallback(TransitionCallback):
        """Transition Callback"""

    jwf.add(
        Flow(
            "flow1",
            Flow1Callback,
            title="Demo flow",
            description="This is config parameter for flow",
        )
        .add(
            Task("task1", Task1Callback, title="Task 1",).add(
                Transition("task2", ToTask2Callback, title="Go to Task2"),
            ),
            Task("task2", Task2Callback, title="Task 2").add(
                Transition("task3", ToTask3Callback, title="Go to Task 3"),
                Transition("task4", ToTask4Callback, title="Go to Task 4"),
                Transition("task_end", FromTask2ToTaskEndCallback, title="Go to end"),
            ),
            Task("task3", Task3Callback).add(Transition("task4")),
            Task("task4", Task4Callback).add(Transition("task_end")),
            Task("task_end", TaskEndCallback),
        )
        .start_with("task1")
    )

    # init flask app
    app = flask.Flask(__name__)
    jwf.init_app(app)

    with app.test_request_context():
        assert jwf == get_jembewf()
