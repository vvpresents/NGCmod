import os, sys, time, string
DELIMITERS = ("{", "}", "(", ")", ";", "#")
QUOTES = ('"', "'")
# gl_tokenized_conf, gl_directives_list = [], []

def is_subrange(subrange_start, subrange_end, range_start, range_end, strong_check=False):
    if strong_check:
        if subrange_start > range_start and subrange_end < range_end:
            return True
    elif subrange_start >= range_start and subrange_end <= range_end:
        return True
    return False
#-----------------------------------------------------------------------------------------------------------------------------------------------------------
# print('==================CURRENT VERSION============================================')
def init_nginx_conf(nginx_conf_path_or_var, encoding="utf-8"):
    if  os.path.isfile(nginx_conf_path_or_var):
        f = open(nginx_conf_path_or_var, 'r', encoding=encoding) 
        nginx_conf = f.read()
        f.close()
    else:
        nginx_conf = nginx_conf_path_or_var
    return nginx_conf 

def get_quoting_ranges_and_delimiters(nginx_conf, quotes = QUOTES, delimiters = DELIMITERS, tab_to_whitespace = 4): # находим все закавыченные части конфига и все потенциальные разделители, включая пробельные символы
    quoting_ranges, all_unesc_quotes, delimiters_with_pos = [], [], []
    lenauq = 0 # количество всех неэкраннированных кавычек
    for i in range(len(nginx_conf)):  # ищем все неэкранированные кавычки и разделители, записываем их индексы вместе с самим символом 
        curr_char = nginx_conf[i]
        if i == 0  or ( nginx_conf[i-1] != "\\" ):
            if curr_char in quotes:
                all_unesc_quotes.append([i, curr_char])
                lenauq += 1
            if curr_char in delimiters or (curr_char in string.whitespace):
                if tab_to_whitespace and curr_char == '\t':
                    for n in range(tab_to_whitespace):
                        delimiters_with_pos.append([i+n, ' '])
                delimiters_with_pos.append([i, curr_char])
    if lenauq > 1:  # ищем все корректно закавыченные подстроки, учитывая что могут быть незначимые вложенные кавычки, поиск идет с первой неэкраннированной кавычки
        i = 0
        while i < lenauq:
            second_quote_not_found = True
            curr_range_of_quote = [all_unesc_quotes[i][0], None, all_unesc_quotes[i][1]]
            j = i+1
            while j < lenauq and second_quote_not_found: #  начинаем поиск закрывающей кавычки 
                # print (i, "  << i  j >>", j,  "len curr_range_of_quote =", len(curr_range_of_quote))
                if  (curr_range_of_quote[1] is None) and (curr_range_of_quote[0] != all_unesc_quotes[j][0]) and (curr_range_of_quote[2] == all_unesc_quotes[j][1]):
                    curr_range_of_quote[1] = all_unesc_quotes[j][0]
                    quoting_ranges.append(curr_range_of_quote)
                    curr_range_of_quote = []
                    second_quote_not_found = False
                    i = j
                j+=1
            i+=1 
    # print(quoting_ranges)
    return quoting_ranges, delimiters_with_pos

def get_unquoted_delimiters(quoting_ranges, delimiters_with_pos): # находим незакавыченные разделители, включая пробельные символы
    unq_delimiters_with_pos = []
    for delpos in delimiters_with_pos:
        unquoted = True
        for qrange in quoting_ranges:
            if qrange[0] < delpos[0] < qrange[1]:
                unquoted = False
                break
        if unquoted: 
            unq_delimiters_with_pos.append([delpos[0], delpos[0], delpos[1]])
    # print(unq_delimiters_with_pos)
    return unq_delimiters_with_pos

#не совсем готовый функционал, но работает
def get_whitespaces_amount_at_the_beginning_of_each_line(nginx_conf, unq_delimiters_with_pos):
    whitespaces_amount_at_lines = [-1]
    i, j, curr_whitespaces_amount, line_number = 0, 0, 0, 1
    lenunqdel = len(unq_delimiters_with_pos)
    whitespaces_in_a_row = True
    for delpos in unq_delimiters_with_pos:
        if delpos[2] == '\n':
            first_newline_pos = delpos[0]
            break
    nginx_conf_first_line = nginx_conf[0:first_newline_pos]
    for i, char in enumerate(nginx_conf_first_line):
        if char == ' ' and char == unq_delimiters_with_pos[i][2] and i == unq_delimiters_with_pos[i][0]:
            curr_whitespaces_amount +=1 
        else: 
            break
    whitespaces_amount_at_lines.append( curr_whitespaces_amount )
    i, curr_whitespaces_amount = 0, 0
    while i < lenunqdel:
        delpos = unq_delimiters_with_pos[i]
        if delpos[2] == '\n':
            j = i + 1 
            line_number += 1
            whitespaces_in_a_row = True
            while (j < lenunqdel)  and  unq_delimiters_with_pos[j][2] == ' ' and whitespaces_in_a_row:
                curr_whitespaces_amount +=1 
                if (j+1 < lenunqdel) and ((unq_delimiters_with_pos[j+1][0] - unq_delimiters_with_pos[j][0] != 1) or (unq_delimiters_with_pos[j+1][2] != unq_delimiters_with_pos[j][2])) :
                    whitespaces_in_a_row = False
                j += 1
            i = j - 1
            whitespaces_amount_at_lines.append( curr_whitespaces_amount )
            curr_whitespaces_amount = 0
        i += 1
    # print('whitespaces_amount_at_lines =', whitespaces_amount_at_lines)
    return whitespaces_amount_at_lines

def get_final_delimiters(nginx_conf, unq_delimiters_with_pos): # находим все правильные разделители и пробельные символы, собираем их в диапазоны, по ним уже будем разбивать конфиг
    final_delimiters_with_pos = []
    i, newlines_in_round_brackets_amount = 0, 0
    lenunqdel = len(unq_delimiters_with_pos)
    len_nginx_conf = len(nginx_conf)
    while i < lenunqdel:
        delpos = unq_delimiters_with_pos[i]
        if delpos[2] in ("{", "}", ";"):
            final_delimiters_with_pos.append(delpos) # добавляем как есть, т.к. является разделителем 
        elif delpos[2] == "(":
            j = i 
            while (j < lenunqdel) and unq_delimiters_with_pos[j][2] != ")":
                if unq_delimiters_with_pos[j][2] in string.whitespace:
                    if unq_delimiters_with_pos[j][2] == '\n':
                        newlines_in_round_brackets_amount += 1 # на случай, если в выражении в круглых скобках будут переводы строки
                    unq_delimiters_with_pos[j][2] = 'not a delimiter' # пробельные символы в выражении в круглых скобках не считаем разделителями, поскольку все выражение является одним параметром директивы нжинкса
                j += 1
        elif delpos[2] == "#":
            j = i 
            while (j < lenunqdel) and unq_delimiters_with_pos[j][2] != "\n":
                unq_delimiters_with_pos[j][2] = 'not a delimiter' # пробельные символы, кроме перевода строки, не являюятся разделителями, т.к. являются частью комментария
                j += 1
            if j != lenunqdel: 
                final_delimiters_with_pos.append([unq_delimiters_with_pos[i][0], unq_delimiters_with_pos[j][0] - 1, "comment"])
            else: # на случай, если после комментария нет вообще ничего, то есть он в конце файла
                final_delimiters_with_pos.append([unq_delimiters_with_pos[i][0], len_nginx_conf - 1, "comment"])
        elif delpos[2] in string.whitespace:
            k, j, newlines_amount = i, i + 1, 0
            if delpos[2] == "\n": 
                newlines_amount += 1
            while (j < lenunqdel) and (unq_delimiters_with_pos[j][2] in string.whitespace) and (unq_delimiters_with_pos[j][0] - unq_delimiters_with_pos[k][0] == 1):
                if unq_delimiters_with_pos[j][2] == "\n": 
                    newlines_amount += 1
                k += 1
                j += 1
            final_delimiters_with_pos.append([unq_delimiters_with_pos[i][0], unq_delimiters_with_pos[j-1][0], "whitespaces", newlines_amount + newlines_in_round_brackets_amount])
            newlines_in_round_brackets_amount = 0
            i = j - 1
        i += 1
    # print('FDP = ', final_delimiters_with_pos)
    return final_delimiters_with_pos

def tokenize_nginx_conf(nginx_conf, final_delimiters_with_pos): # получаем список, состоящий из номеров строк и токенов конфига нжинкса, например  [ [2, 'server'], [2, '{'], [3,'server_name'], [3, 'ya.ru'], [3, ';'] ...]
    tokenized_conf = []
    i,k,line_number = 0,0,1
    while i < len(final_delimiters_with_pos):
        # print ( [final_delimiters_with_pos[i][1], nginx_conf[final_delimiters_with_pos[i][1]]] )
        delim_type = final_delimiters_with_pos[i][2]
        curr_parsed_part = [ line_number, nginx_conf[k:final_delimiters_with_pos[i][0]] ]
        if curr_parsed_part[1]:
            # print(final_delimiters_with_pos[i])
            tokenized_conf.append(curr_parsed_part)
        if delim_type != "whitespaces" and delim_type != "comment":
            tokenized_conf.append( [line_number, delim_type] )
        elif delim_type == "comment":
            # print ( [final_delimiters_with_pos[i][1] + 1, nginx_conf[final_delimiters_with_pos[i][1] +1 ]] )
            tokenized_conf.append( [line_number, nginx_conf[final_delimiters_with_pos[i][0]:final_delimiters_with_pos[i][1] + 1]] )    
        k = final_delimiters_with_pos[i][1] + 1
        curr_parsed_part = []
        if delim_type == "whitespaces": 
            line_number += final_delimiters_with_pos[i][3]
        i += 1
    # global gl_tokenized_conf; gl_tokenized_conf = tokenized_conf
    return tokenized_conf

#не совсем готовый функционал, но работает
def formatted_tokenize_nginx_conf(nginx_conf, final_delimiters_with_pos, whitespaces_amount_at_lines):
    tokenized_conf = []
    i,j,k,line_number = 0,0,0,1
    len_whitespaces_amount_at_lines = len(whitespaces_amount_at_lines)
    while i < len(final_delimiters_with_pos):
        # print ( [final_delimiters_with_pos[i][1], nginx_conf[final_delimiters_with_pos[i][1]]] )
        delim_type = final_delimiters_with_pos[i][2]
        curr_parsed_part = [ line_number, whitespaces_amount_at_lines[line_number], nginx_conf[k:final_delimiters_with_pos[i][0]] ]
        if curr_parsed_part[2]:
            # print(final_delimiters_with_pos[i])
            tokenized_conf.append(curr_parsed_part)
        if delim_type != "whitespaces" and delim_type != "comment":
            tokenized_conf.append( [line_number, whitespaces_amount_at_lines[line_number], delim_type] )
        elif delim_type == "comment":
            # print ( [final_delimiters_with_pos[i][1] + 1, nginx_conf[final_delimiters_with_pos[i][1] +1 ]] )
            tokenized_conf.append( [line_number, whitespaces_amount_at_lines[line_number], nginx_conf[final_delimiters_with_pos[i][0]:final_delimiters_with_pos[i][1] + 1]] )    
            # line_number += 1
        k = final_delimiters_with_pos[i][1] + 1
        curr_parsed_part = []
        if delim_type == "whitespaces": 
            line_number += final_delimiters_with_pos[i][3]
        i += 1
    return tokenized_conf

def build_nginx_conf_minimal(tokenized_conf, indent_whitespaces_amount=4, string_whitespaces_amount=1):
    # config, curr_config_string = [f"### THIS CONFIG WAS BUILDED AUTOMATICALLY AS THE PART OF WEBSITE MOVING PROCESS AT {time.strftime('%Y.%m.%d_%H:%M:%S')}"], []
    config, curr_config_string = [], []
    indent_whitespaces = " " * indent_whitespaces_amount
    string_whitespaces = " " * string_whitespaces_amount
    i, j, curr_nesting = 0, 0, 0
    while i < len(tokenized_conf): 
        # print(j, config, curr_config_string)
        curr_part_line, curr_part_elem = tokenized_conf[i][0], tokenized_conf[i][1]
        if curr_part_elem not in ("{", "}", ";") and curr_part_elem[0] != "#" and curr_part_elem[0] != "(":
            curr_config_string.append(curr_part_elem)
        elif curr_part_elem[0] == "(":
            curr_config_string.append(curr_part_elem.replace('\n',''))
        elif curr_part_elem == ";":
            temp_str = string_whitespaces.join(curr_config_string) + curr_part_elem
            config.append(indent_whitespaces * curr_nesting + temp_str)
            j += 1
            curr_config_string = []
        elif curr_part_elem == "{":
            curr_config_string.append(curr_part_elem)
            config.append(indent_whitespaces * curr_nesting + string_whitespaces.join(curr_config_string) )
            j += 1
            curr_nesting += 1
            curr_config_string = []
        elif curr_part_elem == "}":
            curr_config_string.append(curr_part_elem)
            curr_nesting -= 1
            config.append(indent_whitespaces * curr_nesting + string_whitespaces.join(curr_config_string) )
            j += 1
            curr_config_string = []
        elif curr_part_elem[0] == "#":
            if ( curr_part_line == tokenized_conf[i-1][0]) and (tokenized_conf[i-1][1] in ("{", "}", ";") ) :
                config[j-1] += string_whitespaces + curr_part_elem                        
            else:
                if (curr_part_line == tokenized_conf[i-1][0]) and (tokenized_conf[i-1][1][0] != '#'):
                    curr_config_string.append(curr_part_elem)
                    config.append(indent_whitespaces * curr_nesting + string_whitespaces.join(curr_config_string))
                    j += 1
                else:
                    if curr_config_string:
                        config.append(indent_whitespaces * curr_nesting + string_whitespaces.join(curr_config_string))
                        j += 1
                    config.append(indent_whitespaces * curr_nesting + curr_part_elem)
                    j += 1
                curr_config_string = []
        i += 1
    return "\n".join(config)

#не совсем готовый функционал, но работает
def build_nginx_conf_original(tokenized_conf_formatted, whitespaces_amount_at_lines, string_whitespaces_amount=1):
    # config, curr_config_string = [f"### THIS CONFIG WAS BUILDED AUTOMATICALLY AS THE PART OF WEBSITE MOVING PROCESS AT {time.strftime('%Y.%m.%d_%H:%M:%S')}"], []
    config, curr_config_string, lines_numbers = [], [], []
    string_whitespaces = " " * string_whitespaces_amount
    i, j = 1, 0
    len_tokenized_conf_formatted = len(tokenized_conf_formatted)
    curr_config_string_is_assembling, curr_line_first_whitespaces_added = True, False
    while i < len(whitespaces_amount_at_lines) : 
        # print(j, config, curr_config_string)
        # curr_part_line, curr_part_elem = tokenized_conf_formatted[i][0], tokenized_conf_formatted[i][1]
        if  j  < len_tokenized_conf_formatted and tokenized_conf_formatted[j][0] != i :
            config.append('')
        else:
            while ( j  < len_tokenized_conf_formatted and tokenized_conf_formatted[j][0] == i ):
                # (j < len_tokenized_conf_formatted) and curr_config_string_is_assembling:
                if not curr_line_first_whitespaces_added:
                    curr_line_first_whitespaces = " " * tokenized_conf_formatted[j][1] 
                    curr_line_first_whitespaces_added = True
                curr_config_string.append( tokenized_conf_formatted[j][2]  )
                if j + 1 < len_tokenized_conf_formatted and (tokenized_conf_formatted[j+1][0] - tokenized_conf_formatted[j][0]  != 0):
                    curr_config_string_is_assembling = False
                    config.append(curr_line_first_whitespaces + string_whitespaces.join(curr_config_string))
                    curr_config_string = []
                    curr_line_first_whitespaces_added = False
                j += 1
        i += 1
    k = j - 1
    curr_line_first_whitespaces = " " * tokenized_conf_formatted[k][1]
    for k in range(j,len_tokenized_conf_formatted):
        curr_config_string.append( tokenized_conf_formatted[k][2]  )
    config.append(curr_line_first_whitespaces + string_whitespaces.join(curr_config_string))
    return "\n".join(config)

def get_directives_list_Test_1(tokenized_conf):
    # directives_list, curr_context_name_and_argument = [], []
    # i,j,k, context_number = 0,0,0,0
    # len_tokenized_conf = len(tokenized_conf)
    # while i < len_tokenized_conf:
    directives_list, main = [], []
    contexts_start_list, contexts_end_list, all_contexts_pos_list_in_tokenized_conf = [], [], []
    # contexts_se_list = []
    i, context_id = 0, 1
    while  i < len(tokenized_conf):
        # print(tokenized_conf[i][1])
        if tokenized_conf[i][1] == '}' : 
            contexts_end_list.append(i)
            # contexts_se_list.append(tokenized_conf[i][1], '}')
        if tokenized_conf[i][1] == '{'  :
            k = i - 1
            context_start = 0
            context_start_not_found = True
            curr_context_name_and_arguments = []
            while k >= 0 and context_start_not_found :
                if tokenized_conf[k][1] in (";", '{', '}'):
                    context_start_not_found = False
                    context_start = k + 1
                k -= 1
            k = context_start
            while tokenized_conf[k][1][0] == "#":
                k += 1
            contexts_start_list.append(k)
            # contexts_se_list.append( [tokenized_conf[k][1], '{'])
            for n in range(k, i+1):
                if tokenized_conf[n][1][0] != "#" :
                    curr_context_name_and_arguments.append(tokenized_conf[n][1])
            directives_list.append( [-99999, k, -1, curr_context_name_and_arguments ] )
            # context_id += 1
        if contexts_start_list and contexts_end_list:
            all_contexts_pos_list_in_tokenized_conf.extend( (contexts_start_list.pop(), contexts_end_list.pop()) )
        i+=1
    # print ("ALL_ = ", all_contexts_pos_list_in_tokenized_conf)
    # decoded = [ tokenized_conf[i][1] for i in all_contexts_pos_list_in_tokenized_conf ]
    # print ("decoded= ", decoded)
    if directives_list:
        for context in directives_list:
            curr_context_start_pos_in_mod_parsed = all_contexts_pos_list_in_tokenized_conf.index(context[1])
            curr_context_end_line_in_mod_parsed = all_contexts_pos_list_in_tokenized_conf[curr_context_start_pos_in_mod_parsed + 1] 
            context[1] = tokenized_conf[context[1]][0]
            context[2] = tokenized_conf[curr_context_end_line_in_mod_parsed][0]
        if directives_list[0][1] == 1:
            main = [ [0, -1, -1, ["main"] ] ]
        else:
            main = [ [0, 1, directives_list[0][1] - 1, ["main"] ] ] 
    return  main + directives_list

def get_directives_list(tokenized_conf): # получаем список все директив в виде [ [стартовый индекс директивы в tokenized_conf, конечный индекс директивы в tokenized_conf, тип директивы, имя директивы, параметр_1, параметр_2 ... ],  ... ]
    directives_list, main = [], []
    contexts_start_list, contexts_end_list, all_contexts_pos_list_in_tokenized_conf = [], [], []
    i = 0
    while  i < len(tokenized_conf):
        if tokenized_conf[i][1] == ';'  :
            k = i - 1
            directive_start = 0
            directive_start_not_found = True
            curr_directive_name_and_arguments = []
            while k >= 0 and directive_start_not_found:
                if tokenized_conf[k][1] in (";", '{', '}'):
                    directive_start_not_found = False
                    directive_start = k + 1
                k -= 1
            while tokenized_conf[directive_start][1][0] == "#": # на случай, если будут комментарии между директивами
                directive_start += 1
            for n in range(directive_start, i):
                if tokenized_conf[n][1][0] != "#" :
                    curr_directive_name_and_arguments.append(tokenized_conf[n][1])
            directives_list.append( [ directive_start, i, 'simple' ]  + curr_directive_name_and_arguments)
        if tokenized_conf[i][1] == '{'  :
            k = i - 1
            directive_start = 0
            directive_start_not_found = True
            curr_directive_name_and_arguments = []
            while k >= 0 and directive_start_not_found:
                if tokenized_conf[k][1] in (";", '{', '}'):
                    directive_start_not_found = False
                    directive_start = k + 1
                k -= 1
            while tokenized_conf[directive_start][1][0] == "#": # на случай, если будут комментарии между директивами
                directive_start += 1
            contexts_start_list.append(directive_start)
            for n in range(directive_start, i):
                if tokenized_conf[n][1][0] != "#" :
                    curr_directive_name_and_arguments.append(tokenized_conf[n][1])
            directives_list.append( [ directive_start, -1, 'block' ] + curr_directive_name_and_arguments )
        if tokenized_conf[i][1] == '}' : 
            contexts_end_list.append(i)
        if contexts_start_list and contexts_end_list:
            all_contexts_pos_list_in_tokenized_conf.extend( (contexts_start_list.pop(), contexts_end_list.pop()) ) # собираем индексы начала и конца блочных директив в tokenized_conf (т.е. настоящие номера строки хранятся внутри элемента tokenized_conf с этим индексом)
        i+=1
    # print('all_contexts_pos_list_in_tokenized_conf =', all_contexts_pos_list_in_tokenized_conf)
    # print('directives_list =', directives_list)
    if directives_list:
        for context in directives_list:
            if context[2] == 'block':
                curr_context_start_pos_in_mod_parsed = all_contexts_pos_list_in_tokenized_conf.index(context[0])
                curr_context_end_line_in_mod_parsed = all_contexts_pos_list_in_tokenized_conf[curr_context_start_pos_in_mod_parsed + 1] 
                # context[1] = tokenized_conf[context[1]][0]
                context[1] = curr_context_end_line_in_mod_parsed
        # if directives_list[0][1] == 1:
        #     main = [ ['block', -1, -1, ["main"] ] ]
        # else:
        #     main = [ ['block', 1, directives_list[0][1] - 1, ["main"] ] ] 
    # global gl_directives_list; gl_directives_list = main + directives_list
    return  main + directives_list

def get_server_directive_id (i, directives_list):
    k = i + 1
    server_directive_id = { 'listen': [], 'server_name':[] }
    while (k < len(directives_list)) and directives_list[k][1] <= directives_list[i][1]:
        if directives_list[k][3] == 'listen':
            server_directive_id['listen'].extend(directives_list[k][4:])
        elif directives_list[k][3] == 'server_name':
            server_directive_id['server_name'].extend(directives_list[k][4:])
        k += 1
    return server_directive_id
