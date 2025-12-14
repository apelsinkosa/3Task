import argparse
import yaml
import struct
import sys

# Константы команд (Opcode - поле A)
CMD_LOAD_CONST = 6  # Биты 0-2: 6
CMD_READ_MEM   = 2  # Биты 0-2: 2
CMD_WRITE_MEM  = 5  # Биты 0-2: 5
CMD_BSWAP      = 7  # Биты 0-2: 7

def serialize_cmd_2byte(opcode, operand):
    """
    Формирует 2-байтную команду.
    A (3 бита) + B (смещение/константа).
    Значение = (B << 3) | A
    """
    value = (operand << 3) | opcode
    # '<H' означает little-endian unsigned short (2 байта)
    return struct.pack('<H', value)

def serialize_cmd_4byte(opcode, operand):
    """
    Формирует 4-байтную команду.
    A (3 бита) + B (адрес).
    Значение = (B << 3) | A
    """
    value = (operand << 3) | opcode
    # '<I' означает little-endian unsigned int (4 байта)
    return struct.pack('<I', value)

def assemble(input_path, output_path, log_mode):
    try:
        with open(input_path, 'r', encoding='utf-8') as f:
            program = yaml.safe_load(f)
    except Exception as e:
        print(f"Ошибка чтения входного файла: {e}")
        return

    binary_data = bytearray()
    log_output = []
    
    # СЧЕТЧИК КОМАНД (Требование 3)
    command_count = 0

    for cmd in program:
        name = cmd.get('name')
        args = cmd.get('args', {})
        encoded_bytes = None
        
        if name == 'LOAD_CONST':
            const_val = args.get('value')
            encoded_bytes = serialize_cmd_2byte(CMD_LOAD_CONST, const_val)
            log_output.append(f"LOAD_CONST: A={CMD_LOAD_CONST}, B={const_val}")

        elif name == 'READ_MEM':
            offset = args.get('offset')
            encoded_bytes = serialize_cmd_2byte(CMD_READ_MEM, offset)
            log_output.append(f"READ_MEM: A={CMD_READ_MEM}, B={offset}")

        elif name == 'WRITE_MEM':
            addr = args.get('addr')
            encoded_bytes = serialize_cmd_4byte(CMD_WRITE_MEM, addr)
            log_output.append(f"WRITE_MEM: A={CMD_WRITE_MEM}, B={addr}")

        elif name == 'BSWAP':
            addr = args.get('addr')
            encoded_bytes = serialize_cmd_4byte(CMD_BSWAP, addr)
            log_output.append(f"BSWAP: A={CMD_BSWAP}, B={addr}")
        
        else:
            print(f"Неизвестная команда: {name}")
            continue

        if encoded_bytes:
            binary_data.extend(encoded_bytes)
            command_count += 1
            
            # В тестовом режиме выводим байты (Требование 4)
            if log_mode:
                hex_str = ", ".join([f"0x{b:02X}" for b in encoded_bytes])
                print(f"{name}: {hex_str}")

    # Запись бинарного файла (Требование 2)
    try:
        with open(output_path, 'wb') as f:
            f.write(binary_data)
        # Вывод количества команд (Требование 3)
        print(f"Ассемблировано команд: {command_count}")
        print(f"Результат записан в файл: {output_path}")
    except Exception as e:
        print(f"Ошибка записи: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Assembler for UVM')
    parser.add_argument('input', help='Path to input YAML file')
    parser.add_argument('output', help='Path to output binary file')
    parser.add_argument('--log', action='store_true', help='Enable test mode logging')
    
    args = parser.parse_args()
    assemble(args.input, args.output, args.log)