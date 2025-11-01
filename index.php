 
<!DOCTYPE html>
<html lang="en">

<head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>AllSport - Comprehensive Sports Hub</title>
    <link rel="preconnect" href="https://fonts.googleapis.com" />
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
    <link href="https://fonts.googleapis.com/css2?family=Manrope:wght@400;500;600;700&display=swap" rel="stylesheet" />
    <link rel="stylesheet" href="styles.css" />
</head>

<body>
    <div id="app" class="app-shell">
        <!-- Content rendered by app.js -->
    </div>

    <script src="https://unpkg.com/dayjs@1.11.13/dayjs.min.js"></script>
    <script src="https://unpkg.com/dayjs@1.11.13/plugin/utc.js"></script>
    <script src="https://unpkg.com/dayjs@1.11.13/plugin/timezone.js"></script>
    <script>
        dayjs.extend(dayjs_plugin_utc);
        dayjs.extend(dayjs_plugin_timezone);
    </script>
    <script src="data/sports-data.js"></script>
    <script src="app.js" defer></script>
</body>

</html>
