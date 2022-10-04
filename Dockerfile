FROM python:3.7.13-bullseye
WORKDIR E:\Bootcamp_22\Javier\Repositorios\me_gusta_el_furgol

ENV FLASK_APP app_1_0.py
ENV FLASK_RUN_HOST 0.0.0.0

COPY requirements.txt requirements.txt
RUN python -m pip install --upgrade pip
RUN python -m pip install -r requirements.txt

COPY . .                

CMD [ "python", "app_1_0.py" ]

EXPOSE 5000
