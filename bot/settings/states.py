from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

class Passport(StatesGroup):
    passport = State()
    
class Payment(StatesGroup):
    chek = State()