from database import disease_collection

sample_data = [
    {
        "key"         : "Bacterial_spot",
        "name"        : "Bacterial Spot",
        "severity"    : "High",
        "scientific_name": "Xanthomonas campestris pv. vesicatoria",
        "description" : "A bacterial infection causing dark, water-soaked spots on leaves, stems and fruit. Spreads rapidly in warm, wet conditions.",
        "symptoms"    : "Small, dark brown spots with yellow halos on leaves. Spots may merge causing leaf drop. Fruit shows raised, scab-like lesions.",
        "treatment"   : "Apply copper-based bactericides. Remove and destroy infected plant material. Avoid overhead irrigation.",
        "prevention"  : "Use certified disease-free seeds. Rotate crops every 2-3 years. Maintain proper plant spacing for airflow.",
        "causes"      : "Bacterial infection spread by splashing water, contaminated tools, and infected seeds under warm and humid conditions.",
        "references"  : [
            "FAO Plant Protection Guide (2022)",
            "Journal of Plant Pathology Research (2021)"
        ],
    },
    {
        "key"         : "Early_blight",
        "name"        : "Early Blight",
        "severity"    : "Medium",
        "scientific_name": "Alternaria solani",
        "description" : "A fungal disease caused by Alternaria solani, affecting older leaves first then spreading upward through the plant.",
        "symptoms"    : "Dark brown spots with concentric rings forming a target-like pattern. Yellow tissue surrounds spots. Lower leaves affected first.",
        "treatment"   : "Apply chlorothalonil or mancozeb fungicide. Remove infected leaves. Ensure adequate plant nutrition.",
        "prevention"  : "Mulch around plants. Avoid wetting foliage. Practice crop rotation. Plant resistant varieties.",
        "causes"      : "Fungal pathogen thriving in warm, humid environments and plant stress conditions.",
        "references"  : [
            "FAO Crop Disease Manual (2022)",
            "Plant Disease Journal (2021)"
        ],
    },
    {
        "key"         : "Late_blight",
        "name"        : "Late Blight",
        "severity"    : "Critical",
        "scientific_name": "Phytophthora infestans",
        "description" : "Caused by Phytophthora infestans — the same pathogen responsible for the Irish potato famine. Can destroy crops within days.",
        "symptoms"    : "Large, irregular grey-green water-soaked lesions. White mould on leaf undersides in humid conditions. Rapid plant collapse.",
        "treatment"   : "Apply metalaxyl or cymoxanil immediately. Remove and bag infected plants. Do not compost infected material.",
        "prevention"  : "Avoid overhead irrigation. Plant in well-drained soil. Monitor weather forecasts for blight risk days.",
        "causes"      : "Oomycete pathogen favored by cool, wet conditions. Can spread explosively in humid weather.",
        "references"  : [
            "International Plant Protection Convention Report (2022)",
            "Fry, W. (2008). Phytophthora infestans. Molecular Plant Pathology."
        ],
    },
    {
        "key"         : "Leaf_Mold",
        "name"        : "Leaf Mold",
        "severity"    : "Medium",
        "scientific_name": "Passalora fulva",
        "description" : "A fungal disease thriving in high humidity greenhouse environments, caused by Passalora fulva.",
        "symptoms"    : "Pale green to yellow spots on upper leaf surface. Olive-green to brown velvety mould on lower surface.",
        "treatment"   : "Improve ventilation. Apply fungicides containing chlorothalonil. Remove severely infected leaves.",
        "prevention"  : "Reduce humidity below 85%. Increase air circulation. Avoid leaf wetness. Use resistant varieties.",
        "causes"      : "Fungal infection common in greenhouse conditions with high humidity and poor air circulation.",
        "references"  : [
            "Greenhouse Crop Protection Handbook (2021)",
            "Laterrot, H. (1986). Breeding for resistance to leaf mould."
        ],
    },
    {
        "key"         : "Septoria_leaf_spot",
        "name"        : "Septoria Leaf Spot",
        "severity"    : "Medium",
        "scientific_name": "Septoria lycopersici",
        "description" : "One of the most common and damaging tomato diseases, caused by the fungus Septoria lycopersici.",
        "symptoms"    : "Small, circular spots with dark borders and light grey centres. Tiny black dots visible in spot centres.",
        "treatment"   : "Apply copper fungicide or chlorothalonil. Remove lower infected leaves. Stake plants for better airflow.",
        "prevention"  : "Avoid overhead watering. Mulch soil surface. Practice 3-year crop rotation.",
        "causes"      : "Fungal infection promoted by wet foliage and poor air circulation. Spreads via rain splash.",
        "references"  : [
            "FAO Plant Health Bulletin (2022)",
            "Basu, P.K. (1974). Overwintering of Septoria lycopersici. Canadian Plant Disease Survey."
        ],
    },
    {
        "key"         : "Spider_mites",
        "name"        : "Spider Mites",
        "severity"    : "Medium",
        "scientific_name": "Tetranychus urticae",
        "description" : "Tiny arachnids, not insects, that feed on plant cells. Thrive in hot, dry conditions and reproduce rapidly.",
        "symptoms"    : "Fine webbing on leaf undersides. Tiny yellow or white stippling on leaves. Leaves turn bronze and drop.",
        "treatment"   : "Apply miticide or insecticidal soap. Spray water forcefully on undersides of leaves. Introduce predatory mites.",
        "prevention"  : "Maintain adequate soil moisture. Avoid dusty conditions. Monitor plants regularly in hot weather.",
        "causes"      : "Infestation by microscopic mites in hot and dry conditions. Population explodes rapidly above 27°C.",
        "references"  : [
            "Integrated Pest Management Guide (2021)",
            "Helle, W. & Sabelis, M.W. (1985). Spider Mites: Their Biology. Elsevier."
        ],
    },
    {
        "key"         : "Target_Spot",
        "name"        : "Target Spot",
        "severity"    : "Medium",
        "scientific_name": "Corynespora cassiicola",
        "description" : "Caused by the fungus Corynespora cassiicola, affecting leaves, stems and fruit in warm humid climates.",
        "symptoms"    : "Circular brown lesions with concentric rings. Lesions may have yellow margins. Affected leaves drop prematurely.",
        "treatment"   : "Apply azoxystrobin or chlorothalonil. Remove infected leaves. Avoid high humidity around plants.",
        "prevention"  : "Ensure good air circulation. Avoid overhead irrigation. Practice crop rotation.",
        "causes"      : "Fungal pathogen spread through rain splash and contaminated debris. Favoured by warm humid conditions.",
        "references"  : [
            "Crop Protection Science Review (2022)",
            "Jones, J.B. (1991). Target spot of tomato. Florida Cooperative Extension Service."
        ],
    },
    {
        "key"         : "Tomato_Yellow_Leaf_Curl_Virus",
        "name"        : "Yellow Leaf Curl Virus",
        "severity"    : "Critical",
        "scientific_name": "Tomato yellow leaf curl virus (TYLCV)",
        "description" : "A viral disease transmitted by whiteflies that causes severe yield loss. No cure exists once infected.",
        "symptoms"    : "Upward curling and yellowing of leaves. Stunted growth. Flower drop and poor fruit set.",
        "treatment"   : "No cure. Remove and destroy infected plants immediately to prevent spread. Control whitefly populations.",
        "prevention"  : "Use whitefly-resistant varieties. Install insect-proof nets. Apply reflective mulch. Use yellow sticky traps.",
        "causes"      : "Viral infection transmitted exclusively by silverleaf whitefly Bemisia tabaci.",
        "references"  : [
            "International Journal of Virology (2021)",
            "Moriones, E. & Navas-Castillo, J. (2000). Tomato yellow leaf curl virus. Virus Research."
        ],
    },
    {
        "key"         : "Tomato_mosaic_virus",
        "name"        : "Mosaic Virus",
        "severity"    : "High",
        "scientific_name": "Tomato mosaic virus (ToMV)",
        "description" : "A highly contagious viral disease spread by contact, tools and hands. Can persist in soil for years.",
        "symptoms"    : "Mottled light and dark green mosaic pattern on leaves. Leaf distortion and curling. Stunted plant growth.",
        "treatment"   : "No cure. Remove infected plants. Disinfect all tools with bleach solution after use.",
        "prevention"  : "Wash hands before handling plants. Disinfect tools regularly. Do not smoke near plants — tobacco carries the virus.",
        "causes"      : "Viral infection spread through contaminated tools, hands, and clothing. Does not require an insect vector.",
        "references"  : [
            "Plant Virology Handbook (2022)",
            "Lewandowski, D.J. (2000). Tobamovirus. Encyclopedia of Plant Pathology."
        ],
    },
    {
        "key"         : "Healthy",
        "name"        : "Healthy",
        "severity"    : "None",
        "scientific_name": "N/A",
        "description" : "The leaf shows no signs of disease, pest damage or nutrient deficiency. The plant is in good condition.",
        "symptoms"    : "Deep green uniform colour. No spots, lesions or abnormal patterns. Normal leaf shape and texture.",
        "treatment"   : "No treatment needed. Continue regular watering, feeding and monitoring.",
        "prevention"  : "Maintain good cultural practices — proper spacing, watering, fertilisation and crop rotation.",
        "causes"      : "No infection detected.",
        "references"  : [
            "General Tomato Cultivation Guide (2022)",
            "FAO (2022). Good Agricultural Practices for tomato production."
        ],
    },
]


disease_collection.delete_many({})
result = disease_collection.insert_many(sample_data)
print(f"Inserted {len(result.inserted_ids)} disease records successfully.")

for disease in disease_collection.find({}, {"key": 1, "name": 1, "severity": 1, "_id": 0}):
    print(f"  {disease['key']:40} {disease['severity']}")