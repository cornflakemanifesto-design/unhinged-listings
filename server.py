from fastapi import FastAPI, HTTPException, Query, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, HTMLResponse
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
from bson import ObjectId
import os
import logging
from pathlib import Path
from contextlib import asynccontextmanager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# MongoDB connection
MONGO_URL = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
DB_NAME = os.environ.get('DB_NAME', 'unhinged_listings')
ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD', 'changeme')

# Database client (initialized on startup)
client = None
db = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage database connection lifecycle."""
    global client, db
    client = AsyncIOMotorClient(MONGO_URL)
    db = client[DB_NAME]
    logger.info("Connected to MongoDB")
    # Create indexes
    await db.listings.create_index("category")
    await db.listings.create_index([("sortOrder", 1)])
    await db.listings.create_index([("postedDate", -1)])
    # Seed if empty
    count = await db.listings.count_documents({})
    if count == 0:
        logger.info("Database empty — seeding initial listings...")
        await seed_initial_data()
    yield
    client.close()
    logger.info("Disconnected from MongoDB")


app = FastAPI(title="Unhinged Listings", lifespan=lifespan)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# --- Pydantic Models ---

class ListingCreate(BaseModel):
    title: str
    price: float
    status: str = "In Stock"
    image: str = ""
    excerpt: str
    fullText: str
    facebookUrl: str = ""
    category: str
    location: str = "Colorado Springs, CO"
    postedDate: Optional[str] = None  # ISO date string, defaults to now


class ListingUpdate(BaseModel):
    title: Optional[str] = None
    price: Optional[float] = None
    status: Optional[str] = None
    image: Optional[str] = None
    excerpt: Optional[str] = None
    fullText: Optional[str] = None
    facebookUrl: Optional[str] = None
    category: Optional[str] = None
    location: Optional[str] = None


class AdminAuth(BaseModel):
    password: str


# --- Helpers ---

def listing_to_dict(listing) -> dict:
    return {
        "id": str(listing["_id"]),
        "title": listing["title"],
        "price": listing["price"],
        "status": listing["status"],
        "image": listing.get("image", ""),
        "excerpt": listing["excerpt"],
        "fullText": listing["fullText"],
        "facebookUrl": listing.get("facebookUrl", ""),
        "category": listing["category"],
        "location": listing.get("location", "Colorado Springs, CO"),
        "postedDate": listing["postedDate"].isoformat() if isinstance(listing["postedDate"], datetime) else listing["postedDate"],
        "createdAt": listing.get("createdAt", listing["postedDate"]).isoformat() if isinstance(listing.get("createdAt", listing["postedDate"]), datetime) else str(listing.get("createdAt", "")),
        "sortOrder": listing.get("sortOrder", 999),
    }


def verify_admin(password: str):
    if password != ADMIN_PASSWORD:
        raise HTTPException(status_code=401, detail="Invalid password")


# --- API Routes ---

@app.get("/api/listings")
async def get_listings(category: Optional[str] = Query(None)):
    query = {}
    if category and category != "all":
        query["category"] = category
    cursor = db.listings.find(query).sort("sortOrder", 1)
    listings = await cursor.to_list(length=200)
    return [listing_to_dict(l) for l in listings]


@app.get("/api/listings/{listing_id}")
async def get_listing(listing_id: str):
    if not ObjectId.is_valid(listing_id):
        raise HTTPException(status_code=404, detail="Listing not found")
    listing = await db.listings.find_one({"_id": ObjectId(listing_id)})
    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")
    return listing_to_dict(listing)


@app.get("/api/categories")
async def get_categories():
    settings = await db.site_settings.find_one({"_id": "site"})
    if settings and "categories" in settings:
        return settings["categories"]
    return DEFAULT_SETTINGS["categories"]


# --- Settings Routes ---

DEFAULT_SETTINGS = {
    "siteTitle": "unhinged listings",
    "subtitle": "colorado springs > for sale / wanted > general for sale",
    "tagline": "where mundane commerce meets existential dread",
    "description": "real items for sale, written through the lens of late-stage capitalism and fourth-wall-breaking nihilism",
    "categories": [
        {"id": "all", "name": "All Listings"},
        {"id": "household", "name": "Household Items"},
        {"id": "furniture", "name": "Furniture"},
        {"id": "tools", "name": "Tools & Equipment"},
        {"id": "vintage", "name": "Vintage & Collectibles"},
    ],
    "safetyTips": "meet in public places\ndon't wire money\navoid offers that seem too good\nbeware of existential dread",
    "footerText": "unhinged listings | all rights reserved to question reality through commerce",
    "footerLinks": "help | safety | privacy | feedback | craigslist blog | best of craigslist | existential crisis support",
    "aboutTitle": "About Unhinged Listings",
    "aboutIntro": "This is an ongoing performance art piece disguised as classified ads. Each listing starts as a real item for sale from my actual home, but transforms into absurdist literature that questions the nature of consumer culture, late-stage capitalism, and the commodification of our lives.",
    "aboutProcess": "Find real item to sell from my home\nStart writing \"normal\" classified ad\nLet nihilistic stream-of-consciousness take over\nBreak fourth wall, question existence\nPost to Facebook Marketplace as functional ad\nArchive here as art piece",
    "aboutQuote": "Full disclosure, this chair does not make you weightless. The laws of universe still apply. I called the manufacturer to complain and they told me that I should shove the chair somewhere inappropriate. I told them I'd already done that but I still wasn't weightless.",
    "aboutQuoteSource": "From the Zero Gravity Chair listing",
    "aboutPhilosophy": "What if classified ads were honest? What if they revealed not just the condition of our possessions, but the condition of our souls? Through intentional existential spirals and absurdist descriptions, these \"ads\" become literature that questions why we buy, why we sell, and why we pretend any of this makes sense.",
    "aboutAuthenticity": "All items are real and actually for sale. The Facebook Marketplace links lead to the live ads (when active). Some sell, some don't, but all serve as both functional commerce and performance art. The unhinged descriptions are posted exactly as written to actual buyers on Facebook Marketplace.",
    "aboutWarning": "Reading these listings may cause existential questioning about the nature of capitalism, the meaning of ownership, and why we accumulate objects only to eventually sell them to strangers on the internet.",
    "contactText": "Serious inquiries only. Cash preferred. Must be able to handle existential conversations about the nature of commerce.",
}


@app.get("/api/settings")
async def get_settings():
    settings = await db.site_settings.find_one({"_id": "site"})
    if settings:
        settings.pop("_id", None)
        # Fill in any missing keys with defaults
        for key, val in DEFAULT_SETTINGS.items():
            if key not in settings:
                settings[key] = val
        return settings
    return DEFAULT_SETTINGS


@app.put("/api/admin/settings")
async def update_settings(request: Request, password: str = Query(...)):
    verify_admin(password)
    data = await request.json()
    data["updatedAt"] = datetime.utcnow().isoformat()
    await db.site_settings.update_one(
        {"_id": "site"},
        {"$set": data},
        upsert=True
    )
    return {"ok": True}


# --- Admin Routes ---

@app.post("/api/admin/verify")
async def admin_verify(auth: AdminAuth):
    verify_admin(auth.password)
    return {"ok": True}


@app.post("/api/admin/listings")
async def create_listing(listing: ListingCreate, password: str = Query(...)):
    verify_admin(password)
    now = datetime.utcnow()
    doc = listing.dict()
    if doc.get("postedDate"):
        try:
            doc["postedDate"] = datetime.fromisoformat(doc["postedDate"])
        except (ValueError, TypeError):
            doc["postedDate"] = now
    else:
        doc["postedDate"] = now
    doc["createdAt"] = now
    doc["updatedAt"] = now
    # Set sortOrder to end of list
    max_order = await db.listings.find_one(sort=[("sortOrder", -1)])
    doc["sortOrder"] = (max_order.get("sortOrder", 0) + 1) if max_order else 0
    result = await db.listings.insert_one(doc)
    created = await db.listings.find_one({"_id": result.inserted_id})
    return listing_to_dict(created)


@app.put("/api/admin/listings/{listing_id}")
async def update_listing(listing_id: str, updates: ListingUpdate, password: str = Query(...)):
    verify_admin(password)
    if not ObjectId.is_valid(listing_id):
        raise HTTPException(status_code=404, detail="Listing not found")
    update_data = {k: v for k, v in updates.dict().items() if v is not None}
    if not update_data:
        raise HTTPException(status_code=400, detail="No fields to update")
    update_data["updatedAt"] = datetime.utcnow()
    result = await db.listings.update_one(
        {"_id": ObjectId(listing_id)},
        {"$set": update_data}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Listing not found")
    updated = await db.listings.find_one({"_id": ObjectId(listing_id)})
    return listing_to_dict(updated)


@app.delete("/api/admin/listings/{listing_id}")
async def delete_listing(listing_id: str, password: str = Query(...)):
    verify_admin(password)
    if not ObjectId.is_valid(listing_id):
        raise HTTPException(status_code=404, detail="Listing not found")
    result = await db.listings.delete_one({"_id": ObjectId(listing_id)})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Listing not found")
    return {"ok": True, "deleted": listing_id}


@app.put("/api/admin/reorder")
async def reorder_listings(request: Request, password: str = Query(...)):
    verify_admin(password)
    data = await request.json()
    order = data.get("order", [])  # list of listing IDs in desired order
    for i, lid in enumerate(order):
        if ObjectId.is_valid(lid):
            await db.listings.update_one(
                {"_id": ObjectId(lid)},
                {"$set": {"sortOrder": i}}
            )
    return {"ok": True}


# --- Seed Data ---

async def seed_initial_data():
    mock_listings = [
        {
            "title": "8 Gal Stainless Steel Round Garbage Can",
            "price": 15,
            "status": "Out of Stock",
            "image": "https://customer-assets.emergentagent.com/job_chaos-pages/artifacts/relva4hw_Garbage%20can%20screen%20shotme.jpg",
            "excerpt": "Are you unhappy? Do you like life dirty? Don't probably wasn't to own your family dinners... but this well designed and engineered 8 gallon stainless steel top is annoying somewhere in the top of your driveway.",
            "fullText": "Condition: Used - Good\nAre you unhappy? Do you like life dirty? Don't probably wasn't to own your family dinners ore tough your private ladit and never trust insides or elite class or the already oh the flight she is Annoying somewhere already on the floor this is Annoying somewhere, I have like a Wednesday, I'm not. I need to stop drinking this has been used as an outside trash can for a bit but it's still in pretty good condition and it still functions like a trash can. I do not have any issues with the stainless steel at all. Just kicking it's probably made in Bangladesh table makers so quality is good I suppose.\n\nThis well designed and engineered 8 gallon stainless steel can...is suitable in The top of your driveway if you think chickens think something un unspeakable dog to fit in areas like offices, living rooms, restaurant bathrooms. The movable bucket liner for taking bags with a laundry basket or the things maybe you bought that you can't fit that still wants the Moutain of put his vent and how tos a budget that I that's got and put have it and how tos a ladbef timg not but not and that in do our and that halt divorce his wife and acting his kitchen.\n\nThe removable bucket liner for talking with a laundry basket or maybe that has no idea so wood isn't a great option.\n\nSoft close lid\nMade base\nHeavy duty stainless steel\nRemovable bucket liner\n\nNot closing, the style look already a bit cramped with straight jacket in these incredible, living room, restaurant bathroom could make the whole room a bit tidy 'gotta' just clean the Moutain of use. Or don't trust me. This is the shouldnit know it's gonna it one, but if it shouldn't wait unless it were do. I think you want it.\n\n$15",
            "facebookUrl": "https://facebook.com/marketplace/sample1",
            "category": "household",
            "location": "Colorado Springs, CO",
            "postedDate": datetime(2024, 1, 15),
        },
        {
            "title": "Zero Gravity Lounge Chair",
            "price": 20,
            "status": "Sold",
            "image": "https://customer-assets.emergentagent.com/job_chaos-pages/artifacts/6xmy0w1y_gravitychair.jpg",
            "excerpt": "Full disclosure, this chair does not make you weightless. The laws of universe still apply. I called the manufacturer to complain...",
            "fullText": "Listed over a week ago in Manitou Springs\nCondition: Used - Good\n\nZero gravity lounge chair available. In good shape. Full disclosure, this chair does not make you weightless. The laws of universe still apply. I called the manufacturer to complain and they told me that I should shove the chair somewhere inappropriate. I told them I'd already done that but I still wasn't weightless.\n\nThis is a reasonably comfortable chair for outdoor relaxation, assuming you can achieve relaxation in this current timeline. The fabric is intact, the frame is solid, and it reclines to a position that makes you feel like you're surrendering to the void, which honestly might be the most honest marketing I can offer.\n\nPick up only. Cash preferred. Serious inquiries only - I don't have the emotional bandwidth for tire kickers right now.",
            "facebookUrl": "https://facebook.com/marketplace/sample2",
            "category": "furniture",
            "location": "Manitou Springs, CO",
            "postedDate": datetime(2024, 1, 12),
        },
        {
            "title": 'Husky 62"x 24" Adjustable Height Solid Wood Top Workbench',
            "price": 150,
            "status": "In Stock",
            "image": "https://customer-assets.emergentagent.com/job_chaos-pages/artifacts/1jjxwsuo_Husky%20table%20screenshot%20me.jpg",
            "excerpt": "I bought this work table about a year ago for $395 because I nearly died several I was about brain because I had it shelve-like it the sub-prime...",
            "fullText": "Listed in Colorado Springs, CO\nCondition: Used - like new\n\nI bought this work table about a year ago for $395 because that I nearly died several I was about brain because I had it shelve-like it the sub-prime reef crisis. Bad joke. Infinite. Hasn't been used never once. Yes. I lied. I've gone to at nearly every repair the height is adjustable but I haven't required this so I can't it get it I disassembled it because I'm lazy and do I need to do everything for everyone?\n\nThis is a heavy-duty table meant for serious work. The tabletop is solid wood, not some particle board that's destined to break somehow. This Husky table is actually made in America. Just kidding. It's probably made in Bangladesh where the labor costs nothing so the history of Bangladesh table makers so quality is good I suppose. The important thing is My brain the size of oil tank thinking is and I just don't have the irony for it anymore. My brain the style for already-a-bric-art-style table straight jacket the ironic. I know it can't that maybe I bought this a bit crapppy and straight jacket making in the chaos and try yet 4 bit due to the matters and try yet that he has to be so god isn't a great option.\n\nRetails for $395\nPriced to move at $150. Price is firm. OBO\n\nThis table has never been assembled and comes in original box. Will help load but won't deliver unless you're offering something interesting in trade. Also, if you're the type of person who shows up without the ability to transport this, we're going to have a problem. Plan accordingly.",
            "facebookUrl": "https://facebook.com/marketplace/sample3",
            "category": "tools",
            "location": "Colorado Springs, CO",
            "postedDate": datetime(2024, 1, 10),
        },
        {
            "title": "Fancy Pants Opera Glasses",
            "price": 40,
            "status": "In Stock",
            "image": "https://customer-assets.emergentagent.com/job_chaos-pages/artifacts/bzvmcl0o_Opera%20glasses%20screenshot.jpg",
            "excerpt": "Two pairs of hoighty-toighty opera glasses. 'Oh dear, those people singing in Italian are so...gay! I'm melancholy at the whole affair...'",
            "fullText": "Listed 3 days ago in Manitou Springs, CO\nCondition: Used - like new\n\nTwo pairs of hoighty-toighty opera glasses.\n\n\"Oh dear, those people singing in Italian are so...gay! I'm melancholy at the whole affair. But wait- that nice fellow on Facebook sold us those pinky-up binoculars that'll make us the talk of the town.\"\n\n\"That's right, my love. Now we can enjoy the show world! I'm dying to squint like those poor people over there! Isn't life grand?\"\n\n\"No dear, it's a horror show. But at least we have the opera.\"\n\nThat's you. After you buy these. You're welcome.\n\nThese are legitimate vintage opera glasses with mother-of-pearl handles and brass construction. They actually work, unlike most things in life. Perfect for pretending you have culture while watching people perform in languages you don't understand, singing about emotions you've forgotten how to feel.\n\nSerious inquiries only. I'm not here to negotiate with people who think $40 is too much for a portal into pretentious enlightenment.",
            "facebookUrl": "https://facebook.com/marketplace/sample4",
            "category": "vintage",
            "location": "Manitou Springs, CO",
            "postedDate": datetime(2024, 1, 18),
        },
        {
            "title": "Ryobi Power Tool Bundle",
            "price": 130,
            "status": "In Stock",
            "image": "https://customer-assets.emergentagent.com/job_chaos-pages/artifacts/hl95airq_Ryobi%20tools%20screenshot.jpg",
            "excerpt": "I finally let my soul, I may have strong feelings about 'JUNK STUFF' and 'why does this guy have a big house-like or 'Why would a person would you care'...",
            "fullText": "Home Improvement Supplies - Tools\nCondition: Used - Good\nBrand: RYOBI\n\nI finally. Ok. You caught me. I may have strong feelings of 'JUNK STUFF' and 'why does this guy have a big house-like or 'Why would a person would you are?'\n\nBut enough about my deep thoughts. This isn't a yard sale or yard-like sale. This is harder. Well. Yes. I did build this. But sorry. This is a basic thing.\n\nLet me just say this: I may have strong feelings or thoughts about 'JUNK STUFF' and 'why does this guy have a house-like Ryobi' and 'why Woodal aren't people like what makes me people like. What would or knows? Junk but intelligent, poor. You ignored of a time. I answered it.\n\nBut seriously, buy this RYOBI starter collection bundle kit grouping thing because i can't still, $499 now 'different' to actually fix stuff if you're weird like that.\n\nIncludes:\n- Drill\n- Circular saw\n- Reciprocating saw\n- Jigsaw\n- Grinder 4' and 4.5' not battery\n- 4 battery-handed not not better 3\n- 2 and 5 Ah\n- 4 battery\n- One Battery\n- Charger\n- Big Bag Some sawdust and dog fur\n\nBought new, all of this would cost you more than I make in a month. OK wait everything, Of don't trust me. This is the shouldn't do anything you so easily, but if it shouldn't wait unless we can actually trust me, I should note, This is the same as doing something from credibility and a negative hepatitis text.\n\nThank you for your cooperation.\nAll standard saw oil and Stanley woodworking handplanes from the 1950s.\n\nI will only meet in well-lit seclusion stations with a lot of people there, or without that, I prefer I am from the past without being written or confronted from credibility and a negative hepatitis test.",
            "facebookUrl": "https://facebook.com/marketplace/sample5",
            "category": "tools",
            "location": "Manitou Springs, CO",
            "postedDate": datetime(2024, 1, 16),
        },
    ]

    for listing in mock_listings:
        listing["createdAt"] = datetime.utcnow()
        listing["updatedAt"] = datetime.utcnow()

    await db.listings.insert_many(mock_listings)
    logger.info(f"Seeded {len(mock_listings)} listings")


# --- Serve Frontend ---

# Mount static files
STATIC_DIR = Path(__file__).parent / "static"
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


@app.get("/")
async def serve_index():
    return FileResponse(str(STATIC_DIR / "index.html"))


# Catch-all for client-side routing (hash-based, but just in case)
@app.get("/{path:path}")
async def catch_all(path: str):
    # Try to serve static file first
    static_file = STATIC_DIR / path
    if static_file.exists() and static_file.is_file():
        return FileResponse(str(static_file))
    # Otherwise serve index.html
    return FileResponse(str(STATIC_DIR / "index.html"))
