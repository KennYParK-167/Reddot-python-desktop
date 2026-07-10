echo " ==> Application Lancer... Pour le fermer veuillez fermer cette fenttre d'invite de comande et ne l'ouvrez qu'une fois <=="
cd server
python -m uvicorn main:app --reload --port 8000
