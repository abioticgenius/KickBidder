# KickBidder

This project is a Football Player Auction Bot designed for Discord. It automates the process of scraping football player data from a website and categorizes players based on their leagues. The data is stored in a JSON file (`auction-sets.json`) which can be used for running football auctions within a Discord bot.

## Features

- **Web Scraping:** Automatically scrape player data from a specified website.
- **League Classification:** Players are categorized based on their leagues.
- **JSON Output:** Player data is stored in a JSON file, making it easy to use for further processing.
- **Discord Integration:** The JSON file can be integrated into a Discord bot to manage football auctions.

## Prerequisites

- Python 3.x
- `requests` library
- `beautifulsoup4` library

## Installation

1. Clone the repository:
    ```sh
    git clone https://github.com/your-username/football-auction-bot.git
    cd football-auction-bot
    ```

2. Install the required Python packages:
    ```sh
    pip install requests beautifulsoup4
    ```

## Usage

1. **Scraping Player Data:**

    Update the `url` variable in the `scrape_player_data(url)` function with the URL of the webpage you want to scrape.

    ```python
    url = 'https://example.com/players'  # Replace with the actual URL
    ```

    Run the script to scrape the data and generate the `auction-sets.json` file:
    
    ```sh
    python scrape_players.py
    ```

2. **JSON Output:**

    The script will create a `auction-sets.json` file with the following structure:
    ```json
    {
        "leagues": {
            "Premier League": [
                {
                    "id": 1,
                    "name": "Lionel Messi",
                    "profile_url": "https://example.com/player/1",
                    "base_price": 10000
                },
                ...
            ],
            ...
        }
    }
    ```

## Example JSON Structure

```json
{
    "leagues": {
        "Premier League": [
            {
                "id": 1,
                "name": "Lionel Messi",
                "profile_url": "https://example.com/player/1",
                "base_price": 10000
            },
            {
                "id": 2,
                "name": "Cristiano Ronaldo",
                "profile_url": "https://example.com/player/2",
                "base_price": 10000
            }
        ],
        "La Liga": [
            {
                "id": 3,
                "name": "Luis Suarez",
                "profile_url": "https://example.com/player/3",
                "base_price": 10000
            }
        ]
    }
}
```
## Customization

- **Parsing Logic:** The script is designed to parse HTML based on specific selectors. If the structure of the webpage changes, you'll need to update the selectors accordingly.
- **Base Price:** The base price for players is set to `10000` by default. You can adjust this value in the script as needed.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## Contributing

Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.

## Contact

If you have any questions or suggestions, feel free to reach out to [proshan2004@gmail.com].
