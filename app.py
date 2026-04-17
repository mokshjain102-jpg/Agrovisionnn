from flask import Flask, request, jsonify, render_template, send_from_directory
from flask_cors import CORS
import tensorflow as tf
import numpy as np
from PIL import Image
import hashlib
import io
import os

app = Flask(__name__, template_folder="templates", static_folder="static")
CORS(app)

# LOAD MODEL
model = tf.keras.models.load_model("model.h5")

# Cache for deterministic results
prediction_cache = {}

# 15 PlantVillage Classes
CLASS_NAMES = [
    "Pepper Bell - Bacterial Spot",
    "Pepper Bell - Healthy",
    "Potato - Early Blight",
    "Potato - Late Blight",
    "Potato - Healthy",
    "Tomato - Bacterial Spot",
    "Tomato - Early Blight",
    "Tomato - Late Blight",
    "Tomato - Leaf Mold",
    "Tomato - Septoria Leaf Spot",
    "Tomato - Spider Mites",
    "Tomato - Target Spot",
    "Tomato - Yellow Leaf Curl Virus",
    "Tomato - Mosaic Virus",
    "Tomato - Healthy",
]

DISEASE_DB = {
    "Pepper Bell - Bacterial Spot": {
        "hindi": "शिमला मिर्च - जीवाणु धब्बा रोग",
        "crop": "Pepper Bell (शिमला मिर्च)",
        "severity": "High",
        "description": "Bacterial spot causes dark, water-soaked lesions on leaves, stems and fruits of pepper plants.",
        "symptoms": ["Dark water-soaked spots on leaves", "Yellowing around spots", "Leaf drop in severe cases", "Raised scab-like spots on fruits"],
        "precautions": ["Use certified disease-free seeds", "Avoid overhead irrigation", "Remove infected plant debris", "Rotate crops every 2-3 years"],
        "prevention": ["Apply copper-based bactericides preventively", "Maintain proper plant spacing for air circulation", "Use resistant pepper varieties", "Disinfect tools between plants"],
        "treatment": ["Spray copper hydroxide (2g/L water)", "Apply streptomycin sulfate as foliar spray", "Remove and destroy heavily infected plants", "Use Bordeaux mixture (1%)"],
    },
    "Pepper Bell - Healthy": {
        "hindi": "शिमला मिर्च - स्वस्थ",
        "crop": "Pepper Bell (शिमला मिर्च)",
        "severity": "None",
        "description": "Your pepper plant is healthy! No disease detected.",
        "symptoms": [],
        "precautions": ["Continue regular watering schedule", "Monitor for pests weekly", "Maintain soil pH 6.0-6.8", "Ensure adequate sunlight (6-8 hours)"],
        "prevention": ["Apply organic mulch around base", "Use companion planting with basil/marigold", "Fertilize with balanced NPK every 2 weeks", "Keep garden area clean"],
        "treatment": ["No treatment needed - plant is healthy!", "Continue current care routine", "Add compost for nutrition boost"],
    },
    "Potato - Early Blight": {
        "hindi": "आलू - अगेती अंगमारी",
        "crop": "Potato (आलू)",
        "severity": "Medium",
        "description": "Early blight causes dark brown concentric ring spots (target-like) on older leaves first.",
        "symptoms": ["Dark brown spots with concentric rings", "Yellowing of leaves around spots", "Lower leaves affected first", "Premature defoliation"],
        "precautions": ["Use certified disease-free seed potatoes", "Avoid wetting foliage during irrigation", "Remove volunteer potato plants", "Practice 3-year crop rotation"],
        "prevention": ["Apply mulch to prevent soil splash", "Space plants properly for air flow", "Use resistant varieties like Kufri Jyoti", "Destroy crop residues after harvest"],
        "treatment": ["Spray Mancozeb (2.5g/L water) every 7-10 days", "Apply Chlorothalonil fungicide", "Use copper oxychloride spray", "Remove and destroy infected leaves immediately"],
    },
    "Potato - Late Blight": {
        "hindi": "आलू - पछेती अंगमारी",
        "crop": "Potato (आलू)",
        "severity": "Critical",
        "description": "Late blight is a devastating disease that can destroy entire potato crops within days. Caused by Phytophthora infestans.",
        "symptoms": ["Water-soaked dark patches on leaves", "White fuzzy growth on leaf undersides", "Rapid browning and wilting", "Brown rot in tubers", "Foul smell from infected parts"],
        "precautions": ["Use only certified seed potatoes", "Avoid planting in poorly drained fields", "Monitor weather - high humidity increases risk", "Do NOT store infected tubers"],
        "prevention": ["Prophylactic spraying of Metalaxyl+Mancozeb", "Hill up soil around plants", "Ensure good drainage in field", "Destroy all cull piles and volunteer plants"],
        "treatment": ["Spray Metalaxyl+Mancozeb (2.5g/L) immediately", "Apply Cymoxanil-based fungicide", "Destroy heavily infected plants by burning", "Harvest early if infection is spreading"],
    },
    "Potato - Healthy": {
        "hindi": "आलू - स्वस्थ",
        "crop": "Potato (आलू)",
        "severity": "None",
        "description": "Your potato plant is healthy! No disease detected.",
        "symptoms": [],
        "precautions": ["Maintain consistent moisture", "Hill up soil as plants grow", "Watch for Colorado potato beetle", "Test soil nutrients regularly"],
        "prevention": ["Apply balanced fertilizer (NPK 10-10-20)", "Use organic mulch", "Rotate with legumes/cereals", "Keep field weed-free"],
        "treatment": ["No treatment needed - plant is healthy!", "Continue current care practices"],
    },
    "Tomato - Bacterial Spot": {
        "hindi": "टमाटर - जीवाणु धब्बा रोग",
        "crop": "Tomato (टमाटर)",
        "severity": "High",
        "description": "Bacterial spot causes small, dark, greasy-looking spots on tomato leaves and fruits.",
        "symptoms": ["Small dark greasy spots on leaves", "Spots may have yellow halo", "Raised scabby spots on fruits", "Severe defoliation in wet weather"],
        "precautions": ["Use pathogen-free seeds and transplants", "Avoid working with wet plants", "Remove all crop debris after season", "Do not save seeds from infected fruits"],
        "prevention": ["Apply copper sprays preventively", "Use drip irrigation instead of overhead", "Space plants for good air circulation", "Use resistant tomato varieties"],
        "treatment": ["Copper hydroxide spray (2g/L water)", "Streptomycin spray in early stages", "Remove and destroy infected plant parts", "Apply Bordeaux mixture (1%)"],
    },
    "Tomato - Early Blight": {
        "hindi": "टमाटर - अगेती अंगमारी",
        "crop": "Tomato (टमाटर)",
        "severity": "Medium",
        "description": "Early blight causes characteristic target-like concentric ring spots on lower leaves first.",
        "symptoms": ["Brown spots with concentric rings (target pattern)", "Lower/older leaves affected first", "Yellowing around spots", "Stem cankers possible"],
        "precautions": ["Stake or cage plants for air flow", "Water at base, not on foliage", "Remove lower leaves touching soil", "Clean garden tools regularly"],
        "prevention": ["Mulch around plants to prevent splash", "Rotate crops - don't plant tomato after potato", "Use resistant varieties", "Apply preventive fungicide in humid weather"],
        "treatment": ["Spray Mancozeb (2.5g/L) every 7 days", "Apply Chlorothalonil fungicide", "Remove all infected leaves promptly", "Use neem oil spray as organic option"],
    },
    "Tomato - Late Blight": {
        "hindi": "टमाटर - पछेती अंगमारी",
        "crop": "Tomato (टमाटर)",
        "severity": "Critical",
        "description": "Late blight rapidly destroys tomato plants. Same pathogen that caused the Irish Potato Famine.",
        "symptoms": ["Large dark water-soaked patches", "White mold on leaf undersides", "Stems turn dark brown/black", "Fruits develop greasy brown spots", "Entire plant wilts rapidly"],
        "precautions": ["Monitor weather forecasts for cool wet conditions", "Never compost infected plants", "Remove ALL infected plant material", "Alert neighboring farmers"],
        "prevention": ["Preventive Metalaxyl+Mancozeb spray", "Use resistant varieties (e.g., Legend, Defiant)", "Ensure excellent air circulation", "Avoid evening irrigation"],
        "treatment": ["Spray Metalaxyl+Mancozeb (2.5g/L) urgently", "Apply Dimethomorph-based fungicide", "Destroy severely infected plants immediately", "Harvest remaining healthy fruits early"],
    },
    "Tomato - Leaf Mold": {
        "hindi": "टमाटर - पत्ती फफूंद",
        "crop": "Tomato (टमाटर)",
        "severity": "Medium",
        "description": "Leaf mold causes olive-green to brown velvety patches on the underside of leaves.",
        "symptoms": ["Yellow spots on upper leaf surface", "Olive-green velvety mold underneath", "Leaves curl and wither", "Common in greenhouse/humid conditions"],
        "precautions": ["Improve greenhouse ventilation", "Reduce humidity below 85%", "Avoid leaf wetness", "Space plants wider apart"],
        "prevention": ["Use resistant tomato varieties", "Prune lower leaves for air flow", "Use fans in greenhouse", "Water early morning only"],
        "treatment": ["Apply Chlorothalonil fungicide", "Spray copper-based fungicide", "Remove heavily infected leaves", "Improve ventilation immediately"],
    },
    "Tomato - Septoria Leaf Spot": {
        "hindi": "टमाटर - सेप्टोरिया पत्ती धब्बा",
        "crop": "Tomato (टमाटर)",
        "severity": "Medium",
        "description": "Septoria leaf spot causes many small circular spots with dark borders and gray centers.",
        "symptoms": ["Numerous small circular spots (1-3mm)", "Dark brown border with gray center", "Tiny black dots in spot centers", "Lower leaves affected first, moves upward"],
        "precautions": ["Remove infected leaves immediately", "Avoid overhead watering", "Don't touch wet plants", "Clean up all debris at season end"],
        "prevention": ["Mulch to prevent rain splash", "3-year rotation away from tomatoes", "Use disease-free transplants", "Stake plants to keep off ground"],
        "treatment": ["Spray Mancozeb or Chlorothalonil", "Apply copper fungicide weekly", "Remove all lower infected leaves", "Use baking soda spray (1 tbsp/gallon) as organic option"],
    },
    "Tomato - Spider Mites": {
        "hindi": "टमाटर - मकड़ी कीट",
        "crop": "Tomato (टमाटर)",
        "severity": "High",
        "description": "Two-spotted spider mites suck cell contents from leaves, causing stippling and webbing.",
        "symptoms": ["Tiny yellow/white stippling on leaves", "Fine webbing on leaf undersides", "Leaves turn bronze/brown", "Leaf drop in severe cases", "Tiny moving dots visible with magnifying glass"],
        "precautions": ["Check plants regularly with magnifying glass", "Keep plants well-watered (stressed plants attract mites)", "Avoid dusty conditions", "Don't over-fertilize with nitrogen"],
        "prevention": ["Encourage predatory mites and ladybugs", "Spray water on leaf undersides weekly", "Use reflective mulch", "Maintain healthy soil with compost"],
        "treatment": ["Spray neem oil (5ml/L water)", "Apply insecticidal soap", "Use Abamectin miticide for severe cases", "Release predatory mites (Phytoseiulus persimilis)"],
    },
    "Tomato - Target Spot": {
        "hindi": "टमाटर - लक्ष्य धब्बा",
        "crop": "Tomato (टमाटर)",
        "severity": "Medium",
        "description": "Target spot causes circular brown spots with concentric rings, similar to early blight but caused by different fungus.",
        "symptoms": ["Circular brown spots with target-like rings", "Spots on leaves, stems, and fruits", "Leaves yellow and drop", "Fruit spots are sunken"],
        "precautions": ["Improve air circulation around plants", "Avoid working with wet plants", "Remove plant debris", "Use clean stakes and cages"],
        "prevention": ["Apply fungicide preventively in humid weather", "Rotate crops for 2-3 years", "Use resistant varieties", "Prune for better air flow"],
        "treatment": ["Spray Azoxystrobin fungicide", "Apply Chlorothalonil", "Remove infected plant parts", "Use copper-based spray as organic option"],
    },
    "Tomato - Yellow Leaf Curl Virus": {
        "hindi": "टमाटर - पीला पत्ता मोड़ विषाणु",
        "crop": "Tomato (टमाटर)",
        "severity": "Critical",
        "description": "TYLCV is a devastating viral disease spread by whiteflies. Infected plants produce little to no fruit.",
        "symptoms": ["Severe upward curling of leaves", "Yellowing of leaf margins", "Stunted plant growth", "Flower drop, no fruit set", "Plants look bushy and small"],
        "precautions": ["Control whitefly population aggressively", "Use insect-proof net in nursery", "Remove and destroy infected plants", "Do NOT transplant infected seedlings"],
        "prevention": ["Use TYLCV-resistant varieties", "Install yellow sticky traps for whiteflies", "Use silver reflective mulch", "Apply systemic insecticide (Imidacloprid) to transplants"],
        "treatment": ["NO CURE for viral infection", "Remove and destroy infected plants immediately", "Control whiteflies with Imidacloprid spray", "Protect remaining healthy plants with netting"],
    },
    "Tomato - Mosaic Virus": {
        "hindi": "टमाटर - मोज़ेक विषाणु",
        "crop": "Tomato (टमाटर)",
        "severity": "High",
        "description": "Tomato mosaic virus causes mottled light/dark green pattern on leaves and distorted growth.",
        "symptoms": ["Mottled light and dark green leaf pattern", "Leaf curling and distortion", "Stunted growth", "Reduced fruit size and quality", "Internal browning of fruits"],
        "precautions": ["Wash hands with soap before handling plants", "Don't smoke near plants (tobacco mosaic)", "Disinfect all tools with 10% bleach", "Remove infected plants immediately"],
        "prevention": ["Use virus-free certified seeds", "Dip tools in milk solution between plants", "Use resistant varieties (TMV resistant)", "Control aphids which can spread virus"],
        "treatment": ["NO CURE for viral infection", "Remove and destroy infected plants", "Disinfect entire growing area", "Plant resistant varieties in next season"],
    },
    "Tomato - Healthy": {
        "hindi": "टमाटर - स्वस्थ",
        "crop": "Tomato (टमाटर)",
        "severity": "None",
        "description": "Your tomato plant is healthy! No disease detected.",
        "symptoms": [],
        "precautions": ["Water consistently at soil level", "Provide 6-8 hours direct sunlight", "Support with stakes or cages", "Monitor for pests weekly"],
        "prevention": ["Rotate crops each year", "Add compost to soil before planting", "Mulch to retain moisture", "Prune suckers for better yield"],
        "treatment": ["No treatment needed - plant is healthy!", "Continue good farming practices"],
    },
}

# Seasonal farming tips
KRISHI_TIPS = [
    {"title": "खरीफ की तैयारी", "tip": "June-July mein dhaan, makka, bajra ki buwai karein. Khet ki gehri jutai zaroor karein.", "season": "Kharif", "icon": "🌾"},
    {"title": "रबी फसल सुझाव", "tip": "October-November mein gehun, chana, sarson ki buwai karein. Beej upchaar zaroor karein.", "season": "Rabi", "icon": "🌻"},
    {"title": "सिंचाई प्रबंधन", "tip": "Drip irrigation se 40-60% paani bachta hai. Subah ya shaam ko sinchai karein.", "season": "All", "icon": "💧"},
    {"title": "जैविक खेती", "tip": "Vermicompost aur jeevamrit se mitti ki sehat sudhaarein. Chemical kam use karein.", "season": "All", "icon": "🌿"},
    {"title": "कीट नियंत्रण", "tip": "Neem ka tel (5ml/L) natural pesticide hai. Yellow sticky traps lagayein.", "season": "All", "icon": "🐛"},
    {"title": "मिट्टी की जांच", "tip": "Har 2 saal mein mitti ki jaanch karwayein. pH 6.0-7.5 best hota hai.", "season": "All", "icon": "🧪"},
]

CROP_CALENDAR = [
    {"month": "Jan", "crops": "Aloo harvest, Tamatar nursery", "activity": "रबी फसल देखभाल"},
    {"month": "Feb", "crops": "Shimla Mirch transplant", "activity": "कीट निगरानी"},
    {"month": "Mar", "crops": "Tamatar transplant, Summer veggies", "activity": "सिंचाई बढ़ाएं"},
    {"month": "Apr", "crops": "Lauki, Tori, Karela", "activity": "गर्मी की सब्जियां"},
    {"month": "May", "crops": "Summer crops care", "activity": "मल्चिंग करें"},
    {"month": "Jun", "crops": "Kharif prep, Dhaan nursery", "activity": "खरीफ तैयारी"},
    {"month": "Jul", "crops": "Dhaan transplant, Makka", "activity": "बुवाई का समय"},
    {"month": "Aug", "crops": "Kharif care, Tamatar nursery", "activity": "कीट नियंत्रण"},
    {"month": "Sep", "crops": "Rabi prep, Aloo seed", "activity": "रबी तैयारी"},
    {"month": "Oct", "crops": "Aloo, Tamatar, Mirch sowing", "activity": "बुवाई शुरू"},
    {"month": "Nov", "crops": "Rabi crops care", "activity": "खाद डालें"},
    {"month": "Dec", "crops": "Winter veggies, Matar", "activity": "ठंड से बचाव"},
]


def preprocess(image):
    image = image.resize((224, 224))
    image = np.array(image) / 255.0
    image = np.expand_dims(image, axis=0)
    return image


def get_image_hash(image_bytes):
    return hashlib.md5(image_bytes).hexdigest()


def is_likely_leaf(image):
    """Check if image likely contains a leaf using green color analysis."""
    img_array = np.array(image)
    if len(img_array.shape) < 3 or img_array.shape[2] < 3:
        return False, "Image must be in color (RGB)"

    r, g, b = img_array[:,:,0], img_array[:,:,1], img_array[:,:,2]

    # Check green dominance
    green_mask = (g > r * 0.8) & (g > b * 0.8) & (g > 40)
    green_ratio = np.sum(green_mask) / (img_array.shape[0] * img_array.shape[1])

    # Also check for brown/yellow (diseased leaves)
    brown_mask = (r > 80) & (g > 50) & (b < r * 0.8) & (r > b)
    brown_ratio = np.sum(brown_mask) / (img_array.shape[0] * img_array.shape[1])

    # Check image variance (not a solid color)
    variance = np.var(img_array)
    if variance < 100:
        return False, "Image appears to be a solid color"

    leaf_ratio = green_ratio + brown_ratio
    if leaf_ratio < 0.08:
        return False, "No leaf or plant detected in image"

    return True, "OK"


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/analyze", methods=["POST"])
def analyze():
    if "file" not in request.files:
        return jsonify({"error": True, "message": "❌ कोई फाइल नहीं मिली। कृपया एक leaf photo upload करें।"}), 400

    file = request.files["file"]
    image_bytes = file.read()

    if len(image_bytes) == 0:
        return jsonify({"error": True, "message": "❌ खाली फाइल। कृपया सही photo upload करें।"}), 400

    # Check cache for deterministic results
    img_hash = get_image_hash(image_bytes)
    if img_hash in prediction_cache:
        return jsonify(prediction_cache[img_hash])

    try:
        img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    except Exception:
        return jsonify({"error": True, "message": "❌ Invalid image file। कृपया JPG/PNG photo upload करें।"}), 400

    # Validate leaf
    is_leaf, reason = is_likely_leaf(img)
    if not is_leaf:
        result = {
            "error": True,
            "message": f"❌ यह एक valid leaf/plant photo नहीं है। {reason}। कृपया एक साफ़ leaf (पत्ती) की photo upload करें।",
            "suggestion": "📸 Tips: Clear leaf photo lein, background simple rakhein, close-up lein."
        }
        return jsonify(result), 400

    # Predict
    processed = preprocess(img)
    prediction = model.predict(processed)
    index = int(np.argmax(prediction))
    confidence = float(np.max(prediction)) * 100

    # Low confidence check
    if confidence < 40:
        result = {
            "error": True,
            "message": "⚠️ Model ko is photo se confident result nahi mila। Photo unclear ho sakti hai।",
            "suggestion": "📸 Behtar photo ke liye: Leaf ko seedha camera ke saamne rakhein, natural light mein photo lein।"
        }
        return jsonify(result), 400

    disease_name = CLASS_NAMES[index]
    disease_info = DISEASE_DB.get(disease_name, {})

    is_healthy = "Healthy" in disease_name

    result = {
        "error": False,
        "disease": disease_name,
        "hindi_name": disease_info.get("hindi", ""),
        "crop": disease_info.get("crop", ""),
        "confidence": round(confidence, 2),
        "severity": disease_info.get("severity", "Unknown"),
        "is_healthy": is_healthy,
        "description": disease_info.get("description", ""),
        "symptoms": disease_info.get("symptoms", []),
        "precautions": disease_info.get("precautions", []),
        "prevention": disease_info.get("prevention", []),
        "treatment": disease_info.get("treatment", []),
    }

    # Cache result
    prediction_cache[img_hash] = result
    return jsonify(result)


@app.route("/api/tips")
def get_tips():
    return jsonify(KRISHI_TIPS)


@app.route("/api/calendar")
def get_calendar():
    return jsonify(CROP_CALENDAR)


# ===== AI CHATBOT =====
FARMING_KB = [
    {"keywords": ["tamatar", "tomato", "टमाटर"], "answer": "🍅 **Tamatar ki kheti:**\n\n• **Mausam:** 20-25°C best hai, thand ya zyada garmi mein crop kharab hoti hai\n• **Mitti:** Domat (loamy) mitti best, pH 6.0-7.0\n• **Buwai:** June-July (Kharif) ya Oct-Nov (Rabi)\n• **Sinchai:** Drip irrigation best, har 3-4 din mein paani dein\n• **Khaad:** DAP 50kg + Urea 25kg per acre basal dose, phir 2 hafte baad Urea top dress\n• **Rog:** Early blight, Late blight, Mosaic virus, Leaf curl — regular monitoring zaruri\n• **Upaj:** 80-100 quintal per acre possible"},
    {"keywords": ["aloo", "potato", "आलू"], "answer": "🥔 **Aloo ki kheti:**\n\n• **Mausam:** 15-20°C best, thand ki fasal hai\n• **Mitti:** Balu-domat, acchi drainage wali, pH 5.5-6.5\n• **Buwai:** October-November mein karein\n• **Beej:** Kufri Jyoti, Kufri Pukhraj, Kufri Bahar popular varieties\n• **Sinchai:** Halki aur baar baar, waterlogging se bachen\n• **Khaad:** 10-12 tonne gobar + DAP + Potash per acre\n• **Rog:** Early blight, Late blight — Metalaxyl+Mancozeb spray karein\n• **Khudai:** 90-120 din mein ready"},
    {"keywords": ["mirch", "pepper", "shimla", "मिर्च", "शिमला"], "answer": "🌶️ **Mirch/Shimla Mirch ki kheti:**\n\n• **Mausam:** 20-30°C, nami wala mausam accha\n• **Mitti:** Domat ya balu-domat, pH 6.0-7.0\n• **Buwai:** Nursery June-July, transplant July-Aug\n• **Sinchai:** Regular par halki, jad mein paani na roke\n• **Khaad:** DAP + Potash + Zinc basal, Urea top dress\n• **Rog:** Bacterial spot, anthracnose, leaf curl\n• **Upaj:** Hari mirch 60-80 quintal/acre, Shimla mirch 50-60 quintal/acre"},
    {"keywords": ["gehun", "wheat", "गेहूं"], "answer": "🌾 **Gehun ki kheti:**\n\n• **Mausam:** 15-25°C, Rabi (sardi) ki fasal\n• **Buwai ka samay:** November ka pehla-doosra hafta best\n• **Beej:** HD-2967, WH-1105, PBW-725 popular varieties\n• **Beej dar:** 40-45 kg per acre\n• **Sinchai:** 4-5 sinchai — Crown root, Tillering, Jointing, Flowering, Dough stage par\n• **Khaad:** DAP 50kg + Urea 60kg per acre (do baar mein)\n• **Katai:** April mein, combine se ya haath se"},
    {"keywords": ["dhaan", "chawal", "rice", "धान", "चावल"], "answer": "🌾 **Dhaan ki kheti:**\n\n• **Mausam:** 25-35°C, Kharif ki mukhya fasal\n• **Nursery:** June mein taiyar karein\n• **Ropai:** July mein, 2-3 paudhe per hill\n• **Sinchai:** Khade paani mein, 5-7 cm paani rakhein\n• **Khaad:** DAP 26kg + MOP 15kg + Zinc Sulphate 10kg per acre\n• **Rog:** Blast, Brown spot — Tricyclazole spray\n• **Katai:** October-November mein"},
    {"keywords": ["organic", "jaivik", "जैविक", "bio"], "answer": "🌿 **Jaivik (Organic) Kheti:**\n\n• **Gobar ki khaad:** 8-10 tonne per acre, 3 hafte pehle daalein\n• **Vermicompost:** 2-3 tonne per acre, best organic khaad\n• **Jeevamrit:** 200L paani + 10kg gobar + 10L gaumutra + 2kg besan + 2kg gud — 7 din tak fermant karein\n• **Neem tel:** 5ml/L paani — natural pesticide\n• **Trichoderma:** 2kg per acre mitti mein milayein — fungal rog se bachav\n• **Hara khaad:** Sanai ya dhaincha buwai karke jot dein\n• **Fayda:** Mitti ki sehat sudharti hai, fasal swasth hoti hai, market mein accha daam milta hai"},
    {"keywords": ["sinchai", "paani", "irrigation", "water", "सिंचाई", "पानी"], "answer": "💧 **Sinchai Prabandhan:**\n\n• **Drip Irrigation:** 40-60% paani bachta hai, sabziyon ke liye best\n• **Sprinkler:** Gehun, sarson jaise faslon ke liye\n• **Furrow:** Ganne, tamatar ke liye traditional method\n• **Samay:** Subah ya shaam ko sinchai karein, dopahar mein nahi\n• **Mulching:** Paraali ya plastic mulch se paani ka evaporation 30% kam hota hai\n• **Tip:** Mitti mein ungli daalo — 2 inch tak sookhi ho to paani do\n• **Govt Scheme:** PM Krishi Sinchai Yojana se subsidy milti hai drip/sprinkler par"},
    {"keywords": ["mitti", "soil", "मिट्टी", "bhumi"], "answer": "🧪 **Mitti ki Jaankari:**\n\n• **Domat (Loamy):** Sabse acchi, sabhi faslon ke liye\n• **Balu (Sandy):** Aloo, moongfali, gajar ke liye acchi\n• **Chiknai (Clay):** Dhaan ke liye best, par drainage kam\n• **pH Testing:** Har 2 saal mein karwayein, 6.0-7.5 ideal hai\n• **Acidic mitti:** Chuna (lime) daalein\n• **Alkaline mitti:** Gypsum 2-3 quintal/acre daalein\n• **Organic matter:** Gobar khaad, vermicompost se mitti ki structure sudharta hai\n• **Soil Health Card:** Govt scheme — free mitti jaanch"},
    {"keywords": ["keet", "keetnashak", "pest", "कीट", "kapas", "insect"], "answer": "🐛 **Keet Niyantran (Pest Control):**\n\n• **Neem tel:** 5ml/L paani — aphid, whitefly, caterpillar ke liye\n• **Yellow sticky trap:** Whitefly pakadne ke liye, 8-10 per acre\n• **Pheromone trap:** Fruit borer ke liye, 5 per acre\n• **Beauveria bassiana:** Bio pesticide, 2.5kg per acre spray\n• **Imidacloprid:** Sucking pests ke liye (1ml/3L paani)\n• **Spinosad:** Caterpillar ke liye organic option\n• **IPM:** Integrated Pest Management — pehle bio, phir chemical last resort mein use karein"},
    {"keywords": ["khaad", "fertilizer", "urea", "dap", "खाद", "उर्वरक"], "answer": "🧪 **Khaad aur Urwarak:**\n\n• **DAP (18-46-0):** Buwai ke samay, jad vikas ke liye\n• **Urea (46-0-0):** Top dressing, 2-3 baar dein\n• **MOP (0-0-60):** Phal/fal quality ke liye\n• **Zinc Sulphate:** Dhaan mein zaruri, 10kg/acre\n• **Boron:** Sarson, tamatar mein fal aane ke liye\n• **Organic options:** Gobar khaad, Vermicompost, Jeevamrit\n• **Tip:** Mitti jaanch ke baad hi khaad ka dose decide karein\n• **Warning:** Zyada Urea se paudha kamzor hota hai — santulit matra mein dein"},
    {"keywords": ["mausam", "weather", "barish", "rain", "मौसम", "बारिश"], "answer": "🌦️ **Mausam aur Kheti:**\n\n• **Kharif (June-Oct):** Dhaan, Makka, Soybean, Kapas — barish par depend\n• **Rabi (Nov-Mar):** Gehun, Chana, Sarson, Aloo — sardi ki fasal\n• **Zaid (Mar-Jun):** Moong, Kheera, Tarbuj — garmi ki chhoti fasal\n• **Barish zyada:** Drainage system banayen, fungicide spray rakhein ready\n• **Sukhaa:** Mulching karein, drip irrigation use karein\n• **Thand:** Nursery ko plastic se dhakein, sinchai raat ko karein (frost se bachav)\n• **App:** Meghdoot app se local mausam ki jaankari lein"},
    {"keywords": ["sarson", "mustard", "सरसों"], "answer": "🌻 **Sarson ki kheti:**\n\n• **Mausam:** 15-25°C, Rabi fasal\n• **Buwai:** October ka aakhri hafta best\n• **Beej:** Pusa Bold, RH-749, 2-2.5 kg/acre\n• **Line se line:** 30cm, paudhe se paudhe 10-15cm\n• **Sinchai:** 2-3 sinchai — flower aur fali bante samay zaruri\n• **Khaad:** DAP 35kg + Urea 35kg + Sulphur 10kg per acre\n• **Rog:** White rust, Alternaria — Mancozeb spray\n• **Upaj:** 6-8 quintal/acre"},
    {"keywords": ["chana", "chickpea", "gram", "चना"], "answer": "🫘 **Chana ki kheti:**\n\n• **Mausam:** 15-30°C, kam paani chahiye\n• **Buwai:** October-November\n• **Beej:** 30-35 kg/acre, Rhizobium ka beej upchaar zaruri\n• **Sinchai:** 1-2 sinchai kaafi, zyada paani hanikarak\n• **Khaad:** DAP 20kg + Sulphur 8kg per acre\n• **Rog:** Uktha (Wilt) — Trichoderma se beej upchaar\n• **Upaj:** 8-10 quintal/acre\n• **Tip:** Chane ke baad gehun lagao — mitti mein nitrogen bachta hai"},
    {"keywords": ["ganna", "sugarcane", "गन्ना"], "answer": "🎋 **Ganna ki kheti:**\n\n• **Buwai:** February-March (Basant), October (Sharad)\n• **Beej:** 3 aankh wale tukde, 25-30 quintal/acre\n• **Nali se nali:** 3-4 feet\n• **Sinchai:** Har 10-15 din, garmi mein har hafta\n• **Khaad:** Heavy feeder — Urea 100kg + DAP 50kg + MOP 40kg per acre\n• **Mitti chadhana:** 2-3 baar earthing up zaruri\n• **Rog:** Red rot, Smut — disease-free beej use karein\n• **Katai:** 10-12 mahine mein ready"},
    {"keywords": ["nursery", "नर्सरी", "paudha", "seedling"], "answer": "🌱 **Nursery Management:**\n\n• **Mitti mix:** Garden soil + Gobar khaad + Balu (1:1:1)\n• **Beej upchaar:** Thiram 2g/kg ya Trichoderma 5g/kg beej\n• **Pro tray:** 98/104 cell tray mein cocopeat + vermiculite\n• **Paani:** Rose can se halka paani, subah-shaam\n• **Dhoop:** 50% shade net nursery ke liye best\n• **Transplant:** 25-30 din ki seedling transplant karein, shaam ko karein\n• **Hardening:** Transplant se 3-4 din pehle paani kam kar dein"},
    {"keywords": ["scheme", "yojana", "sarkari", "govt", "subsidy", "योजना", "सरकारी"], "answer": "🏛️ **Sarkari Yojnayen Kisaanon ke liye:**\n\n• **PM-KISAN:** ₹6000/saal seedhe bank account mein\n• **PM Fasal Bima:** Fasal ka insurance, kam premium\n• **PM Krishi Sinchai Yojana:** Drip/Sprinkler par 55-90% subsidy\n• **Soil Health Card:** Free mitti jaanch + khaad sujhaav\n• **Kisan Credit Card:** 3 lakh tak ka loan 4% byaaj par\n• **eNAM:** Online mandi — accha daam milta hai\n• **Paramparagat Krishi:** Organic kheti ke liye ₹50,000/3 saal\n• **Apply:** CSC center ya apne block agriculture office mein jaayein"},
    {"keywords": ["namaste", "hello", "hi", "hey", "hlo", "bhai", "kaise"], "answer": "🙏 **Namaste Kisaan bhai!**\n\nMain AgroVision AI Bot hoon — aapka kheti ka saathi! 🌱\n\nAap mujhse puch sakte ho:\n• Kisi bhi fasal ki kheti kaise karein\n• Rog aur keet ka ilaaj\n• Mitti, khaad, sinchai ki jaankari\n• Sarkari yojnayen\n• Organic kheti ke tips\n\n**Bas apna sawaal poochein!** 😊"},
    {"keywords": ["dhaniya", "coriander", "धनिया"], "answer": "🌿 **Dhaniya ki kheti:**\n\n• **Mausam:** 15-25°C, thandi mein acchi hoti hai\n• **Buwai:** October-November\n• **Beej:** 8-10 kg/acre, beej ko todke (split) boyein\n• **Sinchai:** Halki, har 8-10 din\n• **Khaad:** DAP 20kg + Urea 15kg per acre\n• **Harvest:** Hari patti 40-50 din mein, daana 110-120 din\n• **Tip:** Patti todne se paudha bushy hota hai aur zyada patti aati hai"},
    {"keywords": ["baingan", "brinjal", "eggplant", "बैंगन"], "answer": "🍆 **Baingan ki kheti:**\n\n• **Mausam:** 25-30°C, garmi mein acchi hoti hai\n• **Nursery:** 4-5 hafte ki seedling transplant karein\n• **Paudhe se paudhe:** 60cm, line se line 75cm\n• **Khaad:** Gobar 10 tonne + DAP 50kg + MOP 30kg per acre\n• **Sinchai:** Har 4-5 din, drip best hai\n• **Rog:** Fruit & Shoot borer — Spinosad spray\n• **Upaj:** 100-150 quintal per acre"},
]

SUGGESTED_QUESTIONS = [
    "🍅 Tamatar ki kheti kaise karein?",
    "🥔 Aloo mein bimari lag gayi, kya karein?",
    "🌿 Organic kheti kaise shuru karein?",
    "💧 Sinchai ka best tarika kya hai?",
    "🧪 Mitti ki jaanch kaise karwayein?",
    "🐛 Keet se kaise bachein?",
    "🌾 Gehun ki buwai kab karein?",
    "🏛️ Kisaanon ke liye sarkari yojnayen",
    "🌶️ Mirch ki kheti mein kya dhyaan rakhein?",
    "🧪 Khaad kitni aur kab daalein?",
]

import re

@app.route("/api/chat", methods=["POST"])
def chat():
    data = request.get_json()
    message = data.get("message", "").lower().strip()

    if not message:
        return jsonify({"reply": "🤔 Kuch to poochein! Kheti se related koi bhi sawaal pooch sakte ho.", "suggestions": SUGGESTED_QUESTIONS[:4]})

    # Search knowledge base
    best_match = None
    best_score = 0

    for entry in FARMING_KB:
        score = 0
        for kw in entry["keywords"]:
            if kw.lower() in message:
                score += 1
                # Bonus for exact word match
                if re.search(r'\b' + re.escape(kw.lower()) + r'\b', message):
                    score += 1
        if score > best_score:
            best_score = score
            best_match = entry

    if best_match and best_score > 0:
        # Pick 3 random suggestions excluding current topic
        import random
        other_suggestions = [q for q in SUGGESTED_QUESTIONS if not any(kw.lower() in q.lower() for kw in best_match["keywords"])]
        suggestions = random.sample(other_suggestions, min(3, len(other_suggestions)))
        return jsonify({"reply": best_match["answer"], "suggestions": suggestions})

    # General fallback
    fallback_replies = [
        "🤔 Yeh topic meri knowledge mein nahi hai, par aap kheti se related sawaal poochein — jaise fasal, mitti, khaad, sinchai, rog, keet, sarkari yojnayen, organic kheti wagairah!",
        "🌱 Is baare mein mere paas abhi jaankari nahi hai. Aap in topics par pooch sakte ho: Tamatar, Aloo, Mirch, Gehun, Dhaan, Sarson, Chana, Ganna, Organic kheti, Mitti, Khaad, Sinchai, Keet niyantran, Sarkari yojnayen",
    ]
    import random
    return jsonify({
        "reply": random.choice(fallback_replies),
        "suggestions": random.sample(SUGGESTED_QUESTIONS, 4)
    })


@app.route("/api/suggestions")
def get_suggestions():
    import random
    return jsonify(random.sample(SUGGESTED_QUESTIONS, min(5, len(SUGGESTED_QUESTIONS))))


if __name__ == "__main__":
    os.makedirs("uploads", exist_ok=True)
    app.run(debug=True, port=5000)