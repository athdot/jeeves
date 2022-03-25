# Utilities

horiz_seperator = "=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-="
error_notif = "/!\\"

def p_error(printErr):
    # Get substring length for one line
    # printErr = printErr.upper()
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
        write_log(error_notif + " " + line + " " + error_notif)
        i = dist
    
def p_sep():
    write_log(horiz_seperator)
    
def p_time(timeToOpen):
    time_list = []
    if int(timeToOpen / (60 * 24)) > 0:
        time_list.append(str(int(timeToOpen / (60 * 24))) + " day")
        if int(timeToOpen / (60 * 24)) > 1:
            time_list[len(time_list) - 1] = time_list[len(time_list) - 1] + "s"
    if int(timeToOpen / 60) % 24 > 0:
        time_list.append(str(int(timeToOpen / 60) % 24) + " hour")
        if int(timeToOpen / 60) % 24 > 1:
            time_list[len(time_list) - 1] = time_list[len(time_list) - 1] + "s"
    if timeToOpen % 60 > 0:
        time_list.append(str(timeToOpen % 60) + " minute")
        if timeToOpen % 60 > 1:
            time_list[len(time_list) - 1] = time_list[len(time_list) - 1] + "s"
                    
    if len(time_list) > 2:
        time_list[len(time_list) - 1] = "and " + time_list[len(time_list) - 1]
        time_list = [", " + s for s in time_list]
        time_list[0] = time_list[0][2:]
    else:
        if len(time_list) > 1:
            time_list[len(time_list) - 1] = " and " + time_list[len(time_list) - 1]
            
    return "".join(time_list)

def write_log(write_line, file_name = "log_file.txt"):
    print(write_line)
    with open(file_name, 'a') as log_file:
        log_file.write(str(write_line) + '\n')
        
def reset_log(file_name = "log_file.txt"):
    with open(file_name, 'r+') as log_file:
        log_file.truncate(0)

def synch_time():
    return
