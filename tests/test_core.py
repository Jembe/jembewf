from jembewf import (
    JembeWF,
    Flow,
    FlowCallback,
    State,
    StateCallback,
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
    """Test defining and running simple linear flow with three states"""
    Process, Step = process_step
    jwf = JembeWF()

    jwf.add(
        Flow("flow1")
        .add(
            State("state1").add(
                Transition("state2"),
            ),
            State("state2").add(
                Transition("state3"),
            ),
            State("state3"),
        )
        .start_with("state1")
    )

    # init flask app
    jwf.init_app(app, _db, Process, Step)

    with app_ctx:
        # manualy go throught process
        process1 = jwf.start("flow1")
        current_steps = process1.current_steps()

        assert process1.flow_name == "flow1"
        assert process1.is_running is True
        assert current_steps[0].state_name == "state1"
        assert current_steps[0].is_active is True

        process1.proceed()
        current_steps = process1.current_steps()

        assert current_steps[0].state_name == "state2"
        assert current_steps[0].is_active is True

        process1.proceed()
        assert process1.current_steps() == []
        assert process1.is_running is False
        assert process1.steps[0].is_active is False
        assert process1.steps[0].is_last_step is False
        assert process1.steps[0].state_name == "state1"
        assert process1.steps[0].ended_at is not None
        assert process1.steps[1].is_active is False
        assert process1.steps[1].is_last_step is False
        assert process1.steps[1].state_name == "state2"
        assert process1.steps[1].ended_at is not None
        assert process1.steps[2].is_active is False
        assert process1.steps[2].is_last_step is True
        assert process1.steps[2].state_name == "state3"
        assert process1.steps[2].ended_at is not None

        # go in while loop
        process2 = jwf.start("flow1")
        while process2.is_running:
            process2.proceed()

        assert process2.last_steps()[0].state_name == "state3"


def test_simple_auto_flow(app, app_ctx, _db, process_step):
    """Test defining and running simple linear flow with auto state"""
    Process, Step = process_step
    jwf = JembeWF()

    jwf.add(
        Flow("flow1")
        .add(
            State("state1").add(
                Transition("state2"),
            ),
            State("state2")
            .add(
                Transition("state3"),
            )
            .auto(),
            State("state3"),
        )
        .start_with("state1")
    )

    # init flask app
    jwf.init_app(app, _db, Process, Step)

    with app_ctx:
        # manualy go throught process
        process1 = jwf.start("flow1")
        current_steps = process1.current_steps()

        assert process1.flow_name == "flow1"
        assert process1.is_running is True
        assert current_steps[0].state_name == "state1"
        assert current_steps[0].is_active is True

        process1.proceed()

        process1.proceed()
        assert process1.current_steps() == []
        assert process1.is_running is False
        assert process1.last_steps()[0].state_name == "state3"


def test_demo_flow_definition(app, _db, process_step):
    """Test defining and running demo flow"""
    jwf = JembeWF()

    class Flow1Callback(FlowCallback):
        """Flow1 Callback"""

    class State1Callback(StateCallback):
        """State1 Callback"""

    class State2Callback(StateCallback):
        """State 2 Callback"""

    class State3Callback(StateCallback):
        """State Callback"""

    class State4Callback(StateCallback):
        """State Callback"""

    class StateEndCallback(StateCallback):
        """State Callback"""

    class ToState2Callback(TransitionCallback):
        """ToState2 Callback"""

    class ToState3Callback(TransitionCallback):
        """Transition Callback"""

    class ToState4Callback(TransitionCallback):
        """Transition Callback"""

    class FromState2ToStateEndCallback(TransitionCallback):
        """Transition Callback"""

    jwf.add(
        Flow(
            "flow1",
            Flow1Callback,
            title="Demo flow",
            description="This is config parameter for flow",
        )
        .add(
            State("state1", State1Callback, title="State 1",).add(
                Transition("state2", ToState2Callback, title="Go to State2"),
            ),
            State("state2", State2Callback, title="State 2").add(
                Transition("state3", ToState3Callback, title="Go to State 3"),
                Transition("state4", ToState4Callback, title="Go to State 4"),
                Transition("state_end", FromState2ToStateEndCallback, title="Go to end"),
            ),
            State("state3", State3Callback).add(Transition("state4")),
            State("state4", State4Callback).add(Transition("state_end")),
            State("state_end", StateEndCallback),
        )
        .start_with("state1")
    )

    # init flask app
    jwf.init_app(app, _db, process_step[0], process_step[1])

    with app.test_request_context():
        assert jwf == get_jembewf()
