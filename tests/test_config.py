import sqlalchemy as sa
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


def test_set_process_model_attributes(app, app_ctx, _db):
    """Test defining and running simple linear flow with three tasks"""
    jwf = JembeWF()

    class Process(jembewf.ProcessMixin, _db.Model):
        """Process"""

        my_data_id = sa.Column(
            sa.Integer(),
            sa.ForeignKey("mydata.id"),
        )
        my_data = sa.orm.relationship("MyData", back_populates="process")

    class Step(jembewf.StepMixin, _db.Model):
        """Step"""

    class MyData(_db.Model):
        """My data with one to one backlink to process"""
        __tablename__ = "mydata"
        id = sa.Column(sa.Integer(), primary_key=True)
        process = sa.orm.relationship(Process, back_populates="my_data", uselist=False)

    # create tables
    with app_ctx:
        _db.create_all()

    jwf.add(
        Flow("flow")
        .add(
            Task("start").add(
                Transition("end"),
            ),
            Task("end"),
        )
        .start_with("start")
    )

    # init flask app
    jwf.init_app(app, _db, Process, Step)

    with app_ctx:
        my_data = MyData()
        process = jwf.start("flow", my_data=my_data, other_data="other")

        assert process.id is not None
        assert my_data.id is not None
        assert process.my_data_id == my_data.id
        assert process.variables == {"other_data": "other"}