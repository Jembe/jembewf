# Jembe Workflow Management

Library with simple Workflow implementation for use in Flask with Sqlalchemy. 
JembeWF can be used without Jembe Framework it only depends on Flask, psycopg2, and Flask-SqlAlchemy.

Workflow is defined in Python by extending and combining Process, Step and NextStep classes.

Workflow process execution is supported by SqlAlchemy models where process instances, states and flows are saved.

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
