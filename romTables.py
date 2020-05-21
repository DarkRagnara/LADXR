from rom import ROM
from pointerTable import PointerTable


class Texts(PointerTable):
    END_OF_DATA = (0xfe, 0xff)

    def __init__(self, rom):
        super().__init__(rom, {
            "count": 0x2B0,
            "pointers_addr": 1,
            "pointers_bank": 0x1C,
            "banks_addr": 0x741,
            "banks_bank": 0x1C,
        })


class Entities(PointerTable):
    def __init__(self, rom):
        super().__init__(rom, {
            "count": 0x320,
            "pointers_addr": 0,
            "pointers_bank": 0x16,
            "data_bank": 0x16,
        })

class RoomsTable(PointerTable):
    HEADER = 2

    def _readData(self, rom, bank_nr, pointer):
        bank = rom.banks[bank_nr]
        start = pointer
        pointer += self.HEADER
        while bank[pointer] != 0xFE:
            obj_type = (bank[pointer] & 0xF0)
            if obj_type == 0xE0:
                pointer += 5
            elif obj_type == 0xC0 or obj_type == 0x80:
                pointer += 3
            else:
                pointer += 2
        pointer += 1
        self._addStorage(bank_nr, start, pointer)
        return bank[start:pointer]


class RoomsOverworldTop(RoomsTable):
    def __init__(self, rom):
        super().__init__(rom, {
            "count": 0x080,
            "pointers_addr": 0x000,
            "pointers_bank": 0x09,
            "data_bank": 0x09,
        })


class RoomsOverworldBottom(RoomsTable):
    def __init__(self, rom):
        super().__init__(rom, {
            "count": 0x080,
            "pointers_addr": 0x100,
            "pointers_bank": 0x09,
            "data_bank": 0x1A,
        })


class RoomsIndoorA(RoomsTable):
    # TODO: The color dungeon tables are in the same bank, but the pointer table is after the room data.
    def __init__(self, rom):
        super().__init__(rom, {
            "count": 0x100,
            "pointers_addr": 0x000,
            "pointers_bank": 0x0A,
            "data_bank": 0x0A,
        })


class RoomsIndoorB(RoomsTable):
    # Most likely, this table can be expanded all the way to the end of the bank,
    # giving a few 100 extra bytes to work with.
    def __init__(self, rom):
        super().__init__(rom, {
            "count": 0x0FF,
            "pointers_addr": 0x000,
            "pointers_bank": 0x0B,
            "data_bank": 0x0B,
        })


class BackgroundTable(PointerTable):
    def _readData(self, rom, bank_nr, pointer):
        # Ignore 2 invalid pointers.
        if pointer in (0, 0x1651):
            return bytearray()

        mem = {}
        bank = rom.banks[bank_nr]
        start = pointer
        while bank[pointer] != 0x00:
            addr = bank[pointer] << 8 | bank[pointer + 1]
            amount = (bank[pointer + 2] & 0x3F) + 1
            repeat = (bank[pointer + 2] & 0x40) == 0x40
            vertical = (bank[pointer + 2] & 0x80) == 0x80
            pointer += 3
            for n in range(amount):
                mem[addr] = bank[pointer]
                if not repeat:
                    pointer += 1
                addr += 0x20 if vertical else 0x01
            if repeat:
                pointer += 1
        pointer += 1
        self._addStorage(bank_nr, start, pointer)

        if mem:
            low = min(mem.keys()) & 0xFFE0
            high = (max(mem.keys()) | 0x001F) + 1
            print(hex(start))
            for addr in range(low, high, 0x20):
                print("".join(map(lambda n: ("%02X" % (mem[addr + n])) if addr + n in mem else "  ", range(0x20))))
        return bank[start:pointer]


class BackgroundTilesTable(BackgroundTable):
    def __init__(self, rom):
        super().__init__(rom, {
            "count": 0x25,
            "pointers_addr": 0x052B,
            "pointers_bank": 0x20,
            "data_bank": 0x08,
            "expand_to_end_of_bank": True
        })


class BackgroundAttributeTable(BackgroundTable):
    def __init__(self, rom):
        super().__init__(rom, {
            "count": 0x25,
            "pointers_addr": 0x1C4B,
            "pointers_bank": 0x24,
            "data_bank": 0x24,
        })


class ROMWithTables(ROM):
    def __init__(self, filename):
        super().__init__(filename)

        # Ability to patch any text in the game with different text
        self.texts = Texts(self)
        # Ability to modify rooms
        self.entities = Entities(self)
        self.rooms_overworld_top = RoomsOverworldTop(self)
        self.rooms_overworld_bottom = RoomsOverworldBottom(self)
        self.rooms_indoor_a = RoomsIndoorA(self)
        self.rooms_indoor_b = RoomsIndoorB(self)

        # Backgrounds for things like the title screen.
        # Note: The PointerTable fails to write these back due to how they are overlapping by default.
        #self.background_tiles = BackgroundTilesTable(self)
        #self.background_attributes = BackgroundAttributeTable(self)

    def save(self, filename, *, name=None):
        self.texts.store(self)
        self.entities.store(self)
        self.rooms_overworld_top.store(self)
        self.rooms_overworld_bottom.store(self)
        self.rooms_indoor_a.store(self)
        self.rooms_indoor_b.store(self)
        #self.background_tiles.store(self)
        #self.background_attributes.store(self)
        super().save(filename, name=name)
