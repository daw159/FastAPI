import asyncio
from datetime import UTC, datetime, timedelta
from pathlib import Path

import httpx
from sqlalchemy import delete, select, update

import model
from database import AsyncSessionLocal, engine
from image_utils import PROFILE_PICS_DIR
from main import app

POPULATE_IMAGES_DIR = Path("populate_images")

USERS = [
    {
        "username": "LahoriDude",
        "email": "lahoridude@gmail.com",
        "password": "LahorePassword1!",
        "image": "corey.png",
    },
    {
        "username": "DesiGuy",
        "email": "desiguy@gmail.com",
        "password": "DesiPassword2!",
        # No image - uses default
    },
    {
        "username": "ChaiLover",
        "email": "chailover@gmail.com",
        "password": "ChaiPassword3!",
        "image": "willow.png",
    },
    {
        "username": "CricketFan",
        "email": "cricketfan@gmail.com",
        "password": "CricketPassword4!",
        "image": "farmdogs.png",
    },
    {
        "username": "LahoreFoodie",
        "email": "lahorefoodie@gmail.com",
        "password": "FoodiePassword5!",
        "image": "poppy.png",
    },
    {
        "username": "DesiExplorer",
        "email": "desiexplorer@gmail.com",
        "password": "ExplorerPassword6!",
        "image": "bronx.png",
    },
]

POSTS = [
    {
        "title": "Why Lahore Food Hits Different",
        "content": "There is something special about Lahore food. You can eat a simple plate of daal chawal and be completely satisfied, or go all out with karahi, naan, kebabs, and dessert. The only problem is deciding where to eat.",
    },
    {
        "title": "The Never Ending Search for Good Chai",
        "content": "A good cup of chai can fix almost anything. Bad day? Chai. Guests coming over? Chai. Friends sitting together with nothing to talk about? Make chai and somehow the conversation starts.",
    },
    {
        "title": "Lahore Traffic is a Different Game",
        "content": "You can leave home twenty minutes early, check the traffic before leaving, choose a different route, and still arrive late. Lahore traffic has a way of making every journey an adventure.",
    },
    {
        "title": "My Favorite Pakistani Foods",
        "content": "If I had to choose my favorite Pakistani foods, biryani, chicken karahi, nihari, seekh kebab, and daal chawal would definitely be on the list. And obviously, none of them are complete without naan or roti.",
    },
    {
        "title": "Cricket is Basically a Religion Here",
        "content": "You don't have to be a professional cricketer to have an opinion about cricket in Pakistan. Everyone knows which player should be selected, who should open the innings, and exactly what the captain did wrong.",
    },
    {
        "title": "The Problem With Pakistani Weddings",
        "content": "Pakistani weddings are supposed to be one event, but somehow they turn into an entire season. Dholki, mehndi, baraat, walima, dinners, family gatherings... by the end of it you need another vacation just to recover.",
    },
    {
        "title": "A Walk Around Anarkali",
        "content": "Anarkali has a completely different energy from modern shopping malls. The streets are busy, shops are everywhere, and there is always something interesting to look at. You can go there for one thing and come back with five.",
    },
    {
        "title": "Rain Makes Lahore Beautiful",
        "content": "Lahore looks completely different after rain. The temperature drops, the roads shine, and everyone suddenly wants chai and pakoras. The only problem is that the traffic somehow becomes even worse.",
    },
    {
        "title": "Biryani: A Very Serious Discussion",
        "content": "There are few food debates more serious than biryani. Everyone has an opinion about the perfect amount of masala, potatoes, rice, and meat. Personally, I think a good biryani should be spicy enough to make you reach for the raita.",
    },
    {
        "title": "The Annual Cricket Match With Friends",
        "content": "Playing cricket with friends sounds simple until everyone starts arguing about the teams, the batting order, the last ball, and whether that was actually a catch. Somehow the match takes three hours and nobody agrees on the final score.",
    },
    {
        "title": "University Life in Pakistan",
        "content": "University life is a strange combination of assignments, presentations, exams, friends, chai breaks, and trying to figure out what is actually happening in the lecture. Somehow the semester is always almost over before you realize it.",
    },
    {
        "title": "The Magic of Daal Chawal",
        "content": "Sometimes the simplest food is the best. A good plate of daal chawal with achar and maybe some raita can compete with almost anything. It is comfort food in its purest form.",
    },
    {
        "title": "Why Everyone Loves PSL",
        "content": "The PSL has become one of my favorite times of the year. The matches, rivalries, crowds, commentary, and endless discussions make every game entertaining. Even people who don't normally watch cricket suddenly become experts.",
    },
    {
        "title": "Lahore at Midnight",
        "content": "There is something about Lahore late at night. The roads are quieter in some places, food spots are still open, and you can find people sitting outside having chai. Sometimes the best conversations happen after midnight.",
    },
    {
        "title": "The Great Chana Chaat Debate",
        "content": "Some people like their chana chaat spicy, some want extra chutney, some want more potatoes, and some somehow turn it into a completely different dish. There is no correct recipe, but everyone thinks their version is the best.",
    },
    {
        "title": "Some of My Favorite Pakistani Dramas",
        "content": "Pakistani dramas have a special ability to turn one small family problem into thirty episodes. Still, when the story is good, it becomes impossible to stop watching. You tell yourself you'll watch one episode and suddenly it is 2 AM.",
    },
    {
        "title": "The First Day of Eid",
        "content": "Eid morning has its own feeling. New clothes, getting ready early, meeting family, eating something sweet, and receiving messages from people you haven't talked to in months. The day goes by way too quickly.",
    },
    {
        "title": "Eid Food is a Different Category",
        "content": "Eid breakfast is already enough to put you into a food coma, but then lunch arrives and somehow there is even more food. By the evening you are completely full and someone still asks if you want to eat something.",
    },
    {
        "title": "My Favorite Places to Visit in Lahore",
        "content": "Lahore has so many different places to explore. The old city has history and character, while newer areas have restaurants, cafes, and shopping. Sometimes you don't even need a plan; just going out is enough.",
    },
    {
        "title": "The Joy of Late Night Food",
        "content": "There is something special about eating after midnight. Maybe it is the hunger, maybe it is the company, or maybe everything just tastes better when you should already be sleeping. Lahore definitely has no shortage of late-night food options.",
    },
    {
        "title": "When Guests Come Over",
        "content": "The moment someone says guests are coming, the entire house changes. Suddenly the living room needs cleaning, extra chairs appear from nowhere, and there is enough food to feed twice as many people as actually arrive.",
    },
    {
        "title": "The Pakistani Parent Starter Pack",
        "content": "Every Pakistani household has certain classic questions. Have you eaten? When are you coming home? Why are you using your phone so much? And the most dangerous one: what are you planning to do with your life?",
    },
    {
        "title": "Summer in Lahore",
        "content": "Lahore summers are not something you casually experience. You survive them. The moment you step outside, you immediately regret your decision. The best strategy is cold drinks, air conditioning, and pretending you don't need to go anywhere.",
    },
    {
        "title": "Winter Chai is Superior",
        "content": "Chai is good all year, but winter chai is different. Sitting somewhere warm with a hot cup while the weather outside is cold is one of the simplest pleasures. Add some biscuits or pakoras and it gets even better.",
    },
    {
        "title": "The Search for the Perfect Burger",
        "content": "Finding a really good burger sounds easy until you actually start looking. One place has amazing sauce, another has better meat, another has incredible fries. Eventually you realize you are going to have to try them all.",
    },
    {
        "title": "Friends and Random Plans",
        "content": "The best plans are usually the ones nobody planned properly. Someone sends a message saying 'bahar chalo' and twenty minutes later everyone is trying to decide where to go. Somehow those random outings become the best memories.",
    },
    {
        "title": "Why Pakistani Families Love Functions",
        "content": "There is always a function. Birthday, engagement, wedding, dinner, Eid gathering, family visit, or someone's cousin's event. You might not know half the people there, but somehow you are still expected to attend.",
    },
    {
        "title": "The Art of Bargaining",
        "content": "Shopping in Pakistan teaches you negotiation skills whether you want them or not. You ask the price, the shopkeeper gives a number, you give another number, and eventually both sides pretend they have made a great deal.",
    },
    {
        "title": "My Favorite Street Foods",
        "content": "Street food has a completely different charm. Gol gappay, samosas, pakoras, bun kebabs, chaat, and fries all have their own place. You don't always need an expensive restaurant when a small food stall can deliver something amazing.",
    },
    {
        "title": "The Philosophy of Gol Gappay",
        "content": "Eating gol gappay is not as simple as it looks. First you choose the filling, then the chutney, then somehow the entire thing breaks before you can eat it. And after eating one, you immediately want another.",
    },
    {
        "title": "Watching Cricket With Family",
        "content": "Watching a Pakistan match with family is more stressful than watching it alone. Everyone has an opinion, everyone is shouting advice at the television, and someone always says we are definitely going to lose right before Pakistan starts winning.",
    },
    {
        "title": "The Weekend Routine",
        "content": "Weekends usually start with the promise of being productive. Then you sleep a little longer, have breakfast late, spend time on your phone, meet friends, go out for food, and suddenly it is Sunday night.",
    },
    {
        "title": "A Perfect Sunday in Lahore",
        "content": "A perfect Sunday doesn't need to be complicated. Sleep in, have a proper breakfast, go somewhere with friends or family, eat good food, drink chai, and come home without thinking about Monday for as long as possible.",
    },
    {
        "title": "Why Pakistani Food Needs Raita",
        "content": "Raita is underrated. Spicy biryani without raita feels incomplete, and a plate of kebabs somehow becomes better when there is a little raita on the side. It is basically the peace treaty of Pakistani food.",
    },
    {
        "title": "The Great Coke vs Pepsi Debate",
        "content": "Every friend group eventually ends up discussing which soft drink is better. People have surprisingly strong opinions about it. Personally, I think both are good depending on what you are eating, but try saying that during a serious debate.",
    },
    {
        "title": "Pakistani Parents and Air Conditioning",
        "content": "The air conditioner can be running for five minutes before someone asks who left it on. Then the temperature is raised, someone complains it is too hot, and five minutes later somebody lowers it again. This cycle never ends.",
    },
    {
        "title": "When the Electricity Goes Out",
        "content": "There is a special moment when everything suddenly turns off and the entire house goes silent. Everyone checks their phone, someone asks if the electricity is gone, and within thirty seconds someone has already started complaining about the heat.",
    },
    {
        "title": "The Mystery of Family Group Chats",
        "content": "Family WhatsApp groups are impossible to predict. One morning you get a good morning message, then a random video, then someone's wedding invitation, followed by a political discussion nobody asked for. Somehow there are 147 unread messages before breakfast.",
    },
    {
        "title": "What Makes Lahore Home",
        "content": "Lahore can be chaotic, crowded, noisy, and unbelievably hot, but there is something comforting about it. The food, the people, the old streets, the conversations over chai, and the feeling that there is always somewhere to go make it feel like home.",
    },
    {
        "title": "Hmm... What Else?",
        "content": "I'm running out of ideas for these blog posts. Maybe I should write about Lahore again... Oh wait, I've already done that multiple times. Well, if you're still reading, thanks for sticking around. Now go get yourself some chai.",
    },
]

# The 44th post - always the oldest (easter egg for pagination tutorial)
POST_44 = {
    "title": "Fun Fact: My High School Football Number Was #44",
    "content": "If you've paginated all the way to this post, the 44th one... you get to learn this fun fact: that my high school football number was #44. Other notable absolute legends who wore number #44 include: Jerry West (NBA - Also fellow WV Native), Hank Aaron (MLB), and Floyd Little (NFL).",
}


async def clear_existing_data() -> None:
    # Delete profile pictures from local storage
    if PROFILE_PICS_DIR.exists():
        for file in PROFILE_PICS_DIR.iterdir():
            if file.is_file() and file.name != ".gitkeep":
                file.unlink()
        print(f"Deleted profile pictures from {PROFILE_PICS_DIR}")

    # Clear database tables (order respects foreign keys)
    async with AsyncSessionLocal() as db:
        await db.execute(delete(model.Post))
        await db.execute(delete(model.User))
        await db.commit()
    print("Cleared existing data")


async def update_post_dates() -> None:
    now = datetime.now(UTC)

    async with AsyncSessionLocal() as db:
        result = await db.execute(select(model.Post).order_by(model.Post.id))
        posts = result.scalars().all()

        if not posts:
            return

        # First post (POST_44) is the oldest - ~90 days ago
        await db.execute(
            update(model.Post)
            .where(model.Post.id == posts[0].id)
            .values(date_posted=now - timedelta(days=90)),
        )

        # Remaining posts: each ~1.5 days newer than previous
        for i, post in enumerate(posts[1:], start=1):
            days_ago = (len(posts) - i) * 1.5
            hours_offset = (i * 7) % 24
            post_date = now - timedelta(days=days_ago, hours=hours_offset)
            await db.execute(
                update(model.Post)
                .where(model.Post.id == post.id)
                .values(date_posted=post_date),
            )

        await db.commit()
    print("Updated post dates")


async def populate() -> None:
    transport = httpx.ASGITransport(app=app)

    async with httpx.AsyncClient(
        transport=transport,
        base_url="http://localhost",
    ) as client:
        # Clear existing data (local images first, then database)
        await clear_existing_data()

        users: list[dict] = []

        print(f"\nCreating {len(USERS)} users...")
        for user_data in USERS:
            response = await client.post(
                "/api/users",
                json={
                    "username": user_data["username"],
                    "email": user_data["email"],
                    "password": user_data["password"],
                },
            )
            response.raise_for_status()
            user = response.json()
            print(f"  Created: {user['username']}")

            response = await client.post(
                "/api/users/token",
                data={
                    "username": user_data["email"],
                    "password": user_data["password"],
                },
            )
            response.raise_for_status()
            token = response.json()["access_token"]

            if image_name := user_data.get("image"):
                image_path = POPULATE_IMAGES_DIR / image_name
                if image_path.exists():
                    response = await client.patch(
                        f"/api/users/{user['id']}/picture",
                        files={
                            "file": (
                                image_name,
                                image_path.read_bytes(),
                                "image/png",
                            ),
                        },
                        headers={"Authorization": f"Bearer {token}"},
                    )
                    response.raise_for_status()
                    print(f"    Uploaded: {image_name}")

            users.append(
                {"id": user["id"], "username": user["username"], "token": token},
            )

        print(f"\nCreating {len(POSTS) + 1} posts...")

        # First create POST_44 (will become oldest after date update)
        response = await client.post(
            "/api/posts",
            json={"title": POST_44["title"], "content": POST_44["content"]},
            headers={"Authorization": f"Bearer {users[0]['token']}"},
        )
        response.raise_for_status()
        print(f"  Created: '{POST_44['title']}'")

        # Create remaining posts in reverse (last in list = oldest, first = newest)
        for i, post_data in enumerate(reversed(POSTS)):
            user = users[i % len(users)]
            response = await client.post(
                "/api/posts",
                json={
                    "title": post_data["title"],
                    "content": post_data["content"],
                },
                headers={"Authorization": f"Bearer {user['token']}"},
            )
            response.raise_for_status()
            title = post_data["title"]
            print(
                f"  Created: '{title[:50]}...'"
                if len(title) > 50
                else f"  Created: '{title}'",
            )

        print("\nUpdating post dates...")
        await update_post_dates()

    await engine.dispose()

    print("\nDone!")
    print(f"  {len(USERS)} users")
    print(f"  {len(POSTS) + 1} posts")
    print("  Profile pictures saved locally")


if __name__ == "__main__":
    asyncio.run(populate())