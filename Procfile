web: sh -c 'gunicorn bazaarbot.web.app:app --bind 0.0.0.0:${PORT:-5000} --workers 2 --timeout 120 --access-logfile - --error-logfile -'
