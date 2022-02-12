# Utilities

horiz_seperator = "=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-="
error_notif = "/!\\"

def p_error(printErr):
    # Get substring length for one line
    printErr = printErr.upper()
    sub_len = len(horiz_seperator) - len(error_notif) * 2 - 2 # 2 are spaces
    i = 0
    while i < len(printErr):
        dist = i + sub_len
        if dist > len(printErr):
            dist = len(printErr)
        line = printErr[i:dist]
        if len(line) < sub_len:
            for j in range(len(line), sub_len):
                line = line + " "
        print(error_notif + " " + line + " " + error_notif)
        i = dist
    
def p_sep():
    print(horiz_seperator)