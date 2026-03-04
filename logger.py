def log_debug(message):
    try:
        with open("debug_log.txt", "a", encoding="utf-8") as f:
            f.write(str(message) + "\n")
    except:
        pass
