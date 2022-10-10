# Jembe Workflow Management

Library with simple Workflow implementation for use in Flask with Sqlalchemy. 
JembeWF can be used without Jembe Framework it only depends on Flask and Flask-SqlAlchemy.

Workflow is defined in Python by extending and combining Flow, Task and Transition classes.
Workflow is executed by Process and Step SqlAlchemy persistet instaces that saves information
of process instances (defined by Flow), Step instances (defined by Task).


# Project state

In development

# Usage 

``` python

    from flask_sqlalchemy import SQLAlchemy
    import flask
    import jembewf
    app = flask.Flask(__name__)
    app.config["SQLALCHEMY_DATABASE_URI"] = "postgresql+psycopg2://@/demo"
    db = SQLAlchemy(app=app)

    class Process(jembewf.ProcessMixin, db.Model):
        """Process"""

    class Step(jembewf.StepMixin, db.Model):
        """Step"""

    jwf = JembeWF()

    # Flow definition
    class TaskCallback(jembewf.TaskCallback):
        def callback(self):
            print(self.step)

    jwf.add(
        Flow("flow1")
        .add(
            Task("task1", TaskCallback).add(
                Transition("task2"),
            ),
            Task("task2", TaskCallback).add(
                Transition("task3"),
            ),
            Task("task3", TaskCallback),
        )
        .start_with("task1")
    )
    jwf.init_app(app, db, Process, Step)

    # starting process
    process = jwf.start("flow1")
    # steping thought process
    while process.is_running:
        process.proceed()
```

Output:
```bash
<Step #1: 'task1' from process #1: 'flow1'>
<Step #2: 'task2' from process #1: 'flow1'>
<Step #3: 'task3' from process #1: 'flow1'>
```

## License


Jembe Workflow Management
Copyright (C) 2021 BlokKod <info@blokkod.me>

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU Lesser General Public License as published
by the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU Lesser General Public License for more details.

You should have received a copy of the GNU Lesser General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.
