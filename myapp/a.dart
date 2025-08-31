class _HomeTabState extends State<HomeTab> {
  String username = '';
  String user_image = '';
  bool game1 = false;
  bool game2 = false;
  bool game3 = false;

  @override
  void initState() {
    super.initState();
    loadUsername();
  }

  @override
  void dispose() {
    super.dispose();
  }
Future<void> api() async {
  final prefs = await SharedPreferences.getInstance();
  final token = prefs.getString('token');

  if (token == null || token.isEmpty) {
    print("No token found in SharedPreferences.");
    return;
  }

  final patientId = await getUserId();
  final url = Uri.parse(
      'http://neuron.rubicstechnology.com/api/get_games_name/$patientId');

  final headers = {
    'Content-Type': 'application/json',
    'Authorization': token,
  };

  try {
    final response = await http.get(url, headers: headers);

    if (response.statusCode == 200) {
      final data = jsonDecode(response.body);

      // Map API response to bool values
      game1 = data['game1'] == 1;
      game2 = data['game2'] == 1;
      game3 = data['game3'] == 1;

      print("Game1: $game1, Game2: $game2, Game3: $game3");
    } else {
      print("Error: ${response.statusCode} - ${response.body}");
    }
  } catch (e) {
    print("Exception: $e");
  }
}

  Future<void> loadUsername() async {
    final prefs = await SharedPreferences.getInstance();
    final userJson = prefs.getString('user');

    if (userJson != null) {
      final userData = jsonDecode(userJson);
      print('image value: ${userData['user_image']}');
      setState(() {
        username = userData['username'] ?? 'Patient';
        user_image = userData['user_image'] ?? '';
      });
    } else {
      setState(() {
        username = 'Patient';
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: PreferredSize(
        preferredSize: Size(
          MediaQuery.of(context).size.width,
          MediaQuery.of(context).size.height * 0.12,
        ),
        child: Container(
          color: Color(0xFFEA3B3B),
          child: Padding(
            padding: EdgeInsets.symmetric(vertical: 8.0),
            child: Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Padding(
                  padding: EdgeInsets.only(left: 16.0),
                  child: Row(
                    children: [
                      Image.asset('assets/img/logo.png', width: 40),
                      Column(
                        mainAxisAlignment: MainAxisAlignment.center,
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(
                            "Hello",
                            style: TextStyle(
                              fontFamily: 'Poppins',
                              fontSize:
                                  MediaQuery.of(context).size.width * 0.04,
                              fontWeight: FontWeight.w600,
                              color: Colors.white,
                            ),
                          ),
                          Text(
                            username.isNotEmpty ? username : 'Patient',
                            // 'Safitiri Irma',
                            style: TextStyle(
                              fontFamily: 'Poppins',
                              fontSize:
                                  MediaQuery.of(context).size.width * 0.05,
                              fontWeight: FontWeight.w600,
                              color: Colors.white,
                            ),
                          ),
                        ],
                      ),
                    ],
                  ),
                ),
                Container(
                    margin: EdgeInsets.only(right: 20),
                    child: PopupMenuButton<int>(
                      onSelected: (value) async {
                        if (value == 1) {
                          // Logout tapped
                          final prefs = await SharedPreferences.getInstance();
                          await prefs.clear(); // Clear all stored user data
                          Navigator.of(context, rootNavigator: true)
                              .pushAndRemoveUntil(
                            MaterialPageRoute(builder: (_) => LoginScreen()),
                            (route) => false,
                          );
                        }
                      },
                      itemBuilder: (context) => [
                        PopupMenuItem(
                          value: 1,
                          child: Text(
                            'Logout',
                            style: TextStyle(
                              fontFamily: 'poppins',
                              fontSize: 16,
                              fontWeight: FontWeight.w600,
                            ),
                          ),
                        ),
                      ],
                      child: ClipOval(
                        child: user_image != null && user_image!.isNotEmpty
                            ? Image.network(
                                'https://neuron.rubicstechnology.com$user_image',
                                width: 60,
                                height: 60,
                                fit: BoxFit.cover,
                                errorBuilder: (context, error, stackTrace) {
                                  return Icon(
                                    Icons.person,
                                    size: 60,
                                    color: Colors.white,
                                  );
                                },
                              )
                            : Icon(
                                Icons.person,
                                size: 60,
                                color: Colors.white,
                              ),
                      ),
                    ))
              ],
            ),
          ),
        ),
      ),
      body: Container(
        width: double.infinity,
        child: Column(
          mainAxisAlignment: MainAxisAlignment.spaceEvenly,
          children: [
            Homepagebutton(
              backgroundColor: game1 ? Color(0xFF379EFF) : Color(0xFFEA3B3B),
              imagePath: 'assets/img/Brain.png',
              title: 'Resting State',
              onTap: () {
                playGame("Game-1");
              },
            ),
            Homepagebutton(
              backgroundColor: game2 ? Color(0xFF379EFF) : Color(0xFFEA3B3B),
              imagePath: 'assets/img/Todo_List.png',
              title: 'Continuous Performing Task',
              onTap: () {
                playGame("Game-2");
              },
            ),
            Homepagebutton(
              backgroundColor: game3 ? Color(0xFF379EFF) : Color(0xFFEA3B3B),
              imagePath: 'assets/img/Medium_Icons.png',
              title: 'Visual Stimuli Task',
              onTap: () {
                playGame("Game-3");
              },
            ),
          ],
        ),
      ),
    );
  }

  Future<Map<String, dynamic>> getGameByName({
    required int gameName,
  }) async {
    final prefs = await SharedPreferences.getInstance();
    final token = prefs.getString('token');

    if (token == null || token.isEmpty) {
      print("No token found in SharedPreferences.");
      return {
        'success': false,
        'message': 'Token expired or not found. Please login again.',
      };
    }
    final url = Uri.parse(
        'http://neuron.rubicstechnology.com/api/get-games-by-name-and-patient/');

    final headers = {
      'Content-Type': 'application/json',
      'Authorization': token,
    };

    final patientId = await getUserId();

    final body = jsonEncode({
      'name': gameName,
      'patient_id_fk': patientId,
    });

    try {
      final response = await http.post(url, headers: headers, body: body);

      if (response.statusCode == 200) {
        // Successful response
        return {
          'success': true,
          'data': jsonDecode(response.body),
        };
      } else {
        // Server responded with error
        return {
          'success': false,
          'statusCode': response.statusCode,
          'message': jsonDecode(response.body),
        };
      }
    } catch (e) {
      // Network or decoding error
      return {
        'success': false,
        'error': e.toString(),
      };
    }
  }

  Future<int?> getUserId() async {
    final prefs = await SharedPreferences.getInstance();
    final userString = prefs.getString('user');

    if (userString != null) {
      final userData = jsonDecode(userString);
      return userData['id'];
    }
    return null; // Return null if not found
  }

  Future<void> playGame(String game) async {
    // Navigate to respective screen
    if (game == "Game-1") {
      final result = await getGameByName(gameName: 1);
      if (result['success']) {
        print("Game data: ${result['data']}");
        setState(() {
          game1 = false;
        });
        Navigator.of(context)
            .push(MaterialPageRoute(builder: (context) => RSMode()));
      } else {
        final msg =
            result['message'] ?? result['error'] ?? 'Something went wrong';
        print("Error: $msg");

        final statusCode = result['statusCode'] ?? 'Unknown';

        if (statusCode == 403) {
          print("Server Error (500): $msg");
          setState(() {
            game1 = true;
          });
        } else {
          print("Error ($statusCode): $msg");
        }

        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text((result['message']).toString()),
            backgroundColor: Colors.red,
            duration: Duration(seconds: 3),
          ),
        );
      }
    } else if (game == "Game-2") {
      final result = await getGameByName(gameName: 2);
      if (result['success']) {
        print("Game data: ${result['data']}");
        setState(() {
          game2 = false;
        });
        Navigator.of(context)
            .push(MaterialPageRoute(builder: (context) => CPTMode()));
      } else {
        final msg =
            result['message'] ?? result['error'] ?? 'Something went wrong';
        print("Error: $msg");

        final statusCode = result['statusCode'] ?? 'Unknown';

        if (statusCode == 403) {
          print("Server Error (500): $msg");
          setState(() {
            game2 = true;
          });
        } else {
          print("Error ($statusCode): $msg");
        }

        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text((result['message']['message']).toString()),
            backgroundColor: Colors.red,
            duration: Duration(seconds: 3),
          ),
        );
      }
    } else if (game == "Game-3") {
      final result = await getGameByName(gameName: 3);
      if (result['success']) {
        print("Game data: ${result['data']}");
        setState(() {
          game3 = false;
        });
        Navigator.of(context)
            .push(MaterialPageRoute(builder: (context) => VSTMode()));
      } else {
        final msg =
            result['message'] ?? result['error'] ?? 'Something went wrong';
        print("Error: $msg");

        final statusCode = result['statusCode'] ?? 'Unknown';

        if (statusCode == 403) {
          print("Server Error (500): $msg");
          setState(() {
            game3 = true;
          });
        } else {
          print("Error ($statusCode): $msg");
        }

        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text((result['message']).toString()),
            backgroundColor: Colors.red,
            duration: Duration(seconds: 3),
          ),
        );
      }
    }
  }
}