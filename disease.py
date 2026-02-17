from database import disease_collection

disease_collection.insert_one({
    "name": "Early_blight",
    "causes": [
        "Fungal infection caused by Alternaria solani",
        "High humidity",
        "Poor air circulation"
    ],
    "symptoms": [
        "Dark concentric rings on lower leaves",
        "Yellowing around lesions"
    ],
    "prevention": [
        "Crop rotation",
        "Proper plant spacing",
        "Avoid overhead irrigation"
    ],
    "treatment": [
        "Apply Mancozeb",
        "Use Chlorothalonil fungicide"
    ],
    "chemicals": [
        "Mancozeb",
        "Chlorothalonil"
    ],
    "citations": [
        "FAO Plant Protection Guide 2023",
        "KALRO Tomato Disease Manual"
    ]
})