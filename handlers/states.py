from aiogram.fsm.state import State, StatesGroup

class ProfileStates(StatesGroup):
    registration_date = State()
    position = State()
    first_name = State()
    last_name = State()
    role = State()
    mentor_name = State()
    city = State()
    location = State()
    email = State()
    phone_number = State()
    warpoint_location = State()
    vr_room = State()
    vr_extreme = State()
    attractions = State()
    warcoin = State()
    course = State()

class TestStates(StatesGroup):
    active = State()

class FeedbackStates(StatesGroup):
    waiting_for_feedback = State()