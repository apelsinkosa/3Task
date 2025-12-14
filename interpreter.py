import struct
import argparse
import sys
import xml.etree.ElementTree as ET

# Константы команд
CMD_LOAD_CONST = 6
CMD_READ_MEM   = 2
CMD_WRITE_MEM  = 5
CMD_BSWAP      = 7

class VirtualMachine:
    def __init__(self, mem_size=1024):
        self.memory = [0] * mem_size
        self.accumulator = 0
        self.ip = 0 # Instruction Pointer

    def run(self, program_bytes):
        self.program = program_bytes
        self.ip = 0
        
        while self.ip < len(self.program):
            # Считываем первый байт, чтобы узнать opcode (биты 0-2)
            first_byte = self.program[self.ip]
            opcode = first_byte & 0x7

            if opcode in [CMD_LOAD_CONST, CMD_READ_MEM]:
                # 2-байтные команды
                if self.ip + 2 > len(self.program): break
                cmd_val = struct.unpack('<H', self.program[self.ip:self.ip+2])[0]
                operand = cmd_val >> 3
                self.ip += 2
                
                if opcode == CMD_LOAD_CONST:
                    self.accumulator = operand
                elif opcode == CMD_READ_MEM:
                    # Адрес = Аккумулятор + Смещение (B)
                    addr = self.accumulator + operand
                    if 0 <= addr < len(self.memory):
                        self.accumulator = self.memory[addr]
                    else:
                        print(f"Ошибка: Выход за границы памяти при чтении (Addr: {addr})")

            elif opcode in [CMD_WRITE_MEM, CMD_BSWAP]:
                # 4-байтные команды
                if self.ip + 4 > len(self.program): break
                cmd_val = struct.unpack('<I', self.program[self.ip:self.ip+4])[0]
                operand = cmd_val >> 3
                self.ip += 4
                
                if opcode == CMD_WRITE_MEM:
                    # Запись значения аккумулятора по адресу B
                    addr = operand
                    if 0 <= addr < len(self.memory):
                        self.memory[addr] = self.accumulator
                    else:
                        print(f"Ошибка: Выход за границы памяти при записи (Addr: {addr})")
                
                elif opcode == CMD_BSWAP:
                    # Чтение из памяти по адресу B, bswap, запись в аккумулятор
                    addr = operand
                    if 0 <= addr < len(self.memory):
                        val = self.memory[addr]
                        # Эмуляция bswap (32-bit swap)
                        # Преобразуем в байты (LE), переворачиваем, читаем как (BE) -> или просто перестановка
                        bytes_val = struct.pack('<I', val)
                        swapped_val = struct.unpack('>I', bytes_val)[0]
                        self.accumulator = swapped_val
                    else:
                        print(f"Ошибка: Выход за границы памяти при BSWAP (Addr: {addr})")
            
            else:
                print(f"Неизвестная команда или ошибка выравнивания по адресу {self.ip}")
                break

    def dump_memory(self, path, start_addr, end_addr):
        root = ET.Element("memory")
        for i in range(start_addr, min(end_addr + 1, len(self.memory))):
            cell = ET.SubElement(root, "cell")
            cell.set("address", str(i))
            cell.text = str(self.memory[i])
        
        tree = ET.ElementTree(root)
        ET.indent(tree, space="  ", level=0)
        tree.write(path, encoding="utf-8", xml_declaration=True)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('binary', help='Path to binary file')
    parser.add_argument('result', help='Path to output XML memory dump')
    parser.add_argument('range', help='Memory range to dump (start:end)')
    args = parser.parse_args()

    try:
        start, end = map(int, args.range.split(':'))
    except ValueError:
        print("Ошибка: Диапазон должен быть в формате start:end")
        sys.exit(1)

    vm = VirtualMachine()
    
    try:
        with open(args.binary, 'rb') as f:
            program_bytes = f.read()
        
        vm.run(program_bytes)
        vm.dump_memory(args.result, start, end)
        print(f"Выполнение завершено. Дамп памяти сохранен в {args.result}")
        
    except FileNotFoundError:
        print(f"Файл {args.binary} не найден.")