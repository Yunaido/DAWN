# BillifyPro

## **Understanding the Project Structure**:
   - `billifypro/`: The outer directory is the project container.
   - `billifypro/billifypro/`: The inner directory is the actual Python package for your project.
   - `manage.py`: A command-line utility for interacting with the Django project.

## Running the Development Server

To start the development server and see your project in action, navigate to the project directory

```bash 
cd billifypro 
```
 and run:
```bash
python manage.py runserver
```

Open your web browser and go to `http://127.0.0.1:8000/admin/` to view your project.

## Next Steps

- **Customize Your Project**: Edit the `settings.py` and `urls.py` files to configure your project's settings and URL patterns.

## Migrationen erstellen
Nachdem Sie Ihre Modelle definiert haben, müssen Sie Migrationen erstellen, um die Änderungen in Ihrer Datenbank zu reflektieren. Führen Sie die folgenden Befehle aus:

```bash
python manage.py makemigrations meinapp
```

Dieser Befehl erstellt Migrationsdateien, die die Änderungen an Ihren Modellen darstellen.

## Migrationen anwenden
Um die Migrationen auf Ihre Datenbank anzuwenden und die Änderungen zu übernehmen, führen Sie den folgenden Befehl aus:

```bash
python manage.py migrate
```

## Admin-Site konfigurieren
Um das Django Admin-Site zu nutzen, müssen Sie zunächst einen Superuser erstellen:

```bash
python manage.py createsuperuser
```

Folgen Sie den Anweisungen, um einen Benutzernamen, eine E-Mail-Adresse und ein Passwort zu setzen.