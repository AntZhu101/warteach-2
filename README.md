 # Bot Project

This project is a bot that handles user registration, profile management, training sessions, tests, and feedback collection.

## Project Structure

```
bot_project/
├── bot.py              # Main bot file
├── config.py           # Configuration (API token, data files)
├── states.py           # FSM state definitions
├── handlers/           # Command handlers
│   ├── start.py        # /start command
│   ├── profile.py      # User profile
│   ├── training.py     # Training
│   ├── tests.py        # Testing
│   ├── feedback.py     # Feedback
│   ├── non
├── utils/              # Utility modules
│   ├── json_utils.py   # JSON handling
│   ├── bot_utils.py    # General bot functions
│   ├── course_plan.py  # Course plan creation
├── data/               # Data storage
│   ├── training_data.json   # Training materials
│   ├── feedback/            # Feedback
│   │   ├── feedback.json
│   ├── users/               # User data
│   │   ├── user_xxx.json
├── images/             # Images
├── text                
├── requirements.txt    # Dependencies
└── README.md           # Documentation
```

## Setup

1. Clone the repository.
2. Install the dependencies:
    ```sh
    pip install -r requirements.txt
    ```
3. Create a `.env` file with your API token:
    ```dotenv
    API_TOKEN=your_api_token_here
    ```
4. Run the bot:
    ```sh
    python bot.py
    ```

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.