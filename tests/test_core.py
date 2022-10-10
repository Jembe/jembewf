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
import jembewf


def test_extension_initialisation(app, app_ctx, _db, process_step):
    """Ensure JembeWF is loaded into Flask"""

    jwf = JembeWF()
    jwf.init_app(app, _db, process_step[0], process_step[1])

    with app_ctx:
        assert jwf == get_jembewf()


def test_simple_flow_definition(app, app_ctx, _db, process_step):
    """Test defining and running simple linear flow with three tasks"""
    Process, Step = process_step
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
    jwf.init_app(app, _db, Process, Step)

    with app_ctx:
        # manualy go throught process
        process1 = jwf.start("flow1")
        current_steps = process1.current_steps()

        assert process1.flow_name == "flow1"
        assert process1.is_running is True
        assert current_steps[0].task_name == "task1"
        assert current_steps[0].is_active is True

        process1.proceed()
        current_steps = process1.current_steps()

        assert current_steps[0].task_name == "task2"
        assert current_steps[0].is_active is True

        process1.proceed()
        assert process1.current_steps() == []
        assert process1.is_running is False
        assert process1.steps[0].is_active is False
        assert process1.steps[0].is_last_step is False
        assert process1.steps[0].task_name == "task1"
        assert process1.steps[0].ended_at is not None
        assert process1.steps[1].is_active is False
        assert process1.steps[1].is_last_step is False
        assert process1.steps[1].task_name == "task2"
        assert process1.steps[1].ended_at is not None
        assert process1.steps[2].is_active is False
        assert process1.steps[2].is_last_step is True
        assert process1.steps[2].task_name == "task3"
        assert process1.steps[2].ended_at is not None

        # go in while loop
        process2 = jwf.start("flow1")
        while process2.is_running:
            process2.proceed()

        assert process2.last_steps()[0].task_name == "task3"


def test_simple_auto_flow(app, app_ctx, _db, process_step):
    """Test defining and running simple linear flow with auto task"""
    Process, Step = process_step
    jwf = JembeWF()

    jwf.add(
        Flow("flow1")
        .add(
            Task("task1").add(
                Transition("task2"),
            ),
            Task("task2")
            .add(
                Transition("task3"),
            )
            .auto(),
            Task("task3"),
        )
        .start_with("task1")
    )

    # init flask app
    jwf.init_app(app, _db, Process, Step)

    with app_ctx:
        # manualy go throught process
        process1 = jwf.start("flow1")
        current_steps = process1.current_steps()

        assert process1.flow_name == "flow1"
        assert process1.is_running is True
        assert current_steps[0].task_name == "task1"
        assert current_steps[0].is_active is True

        process1.proceed()

        process1.proceed()
        assert process1.current_steps() == []
        assert process1.is_running is False
        assert process1.last_steps()[0].task_name == "task3"


def test_demo_flow_definition(app, _db, process_step):
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
    jwf.init_app(app, _db, process_step[0], process_step[1])

    with app.test_request_context():
        assert jwf == get_jembewf()
