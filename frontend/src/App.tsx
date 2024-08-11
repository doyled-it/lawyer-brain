import React, { useState, useEffect } from "react";
import { ThemeProvider } from "@mui/material/styles";
import CssBaseline from "@mui/material/CssBaseline";
import Box from "@mui/material/Box";
import AppBar from "@mui/material/AppBar";
import Toolbar from "@mui/material/Toolbar";
import Typography from "@mui/material/Typography";
import FormControlLabel from "@mui/material/FormControlLabel";
import Switch from "@mui/material/Switch";
import Container from "@mui/material/Container";
import { Link, BrowserRouter as Router, Route, Routes } from "react-router-dom";
import Chatbot from "./components/Chatbot";
import About from "./components/About"; // Assuming you have an About component
import { lightTheme, darkTheme } from "./theme";
import { DarkModeTwoTone, LightModeTwoTone } from "@mui/icons-material";

const App: React.FC = () => {
  const [darkMode, setDarkMode] = useState<boolean>(false);

  useEffect(() => {
    const savedThemePreference = localStorage.getItem("darkMode");
    if (savedThemePreference) {
      setDarkMode(savedThemePreference === "true");
    }
  }, []);

  const handleThemeChange = () => {
    setDarkMode(!darkMode);
    localStorage.setItem("darkMode", (!darkMode).toString());
  };

  return (
    <ThemeProvider theme={darkMode ? darkTheme : lightTheme}>
      <CssBaseline />
      <Router>
        <AppBar position="sticky">
          <Toolbar>
            <Link
              to="/"
              style={{
                textDecoration: "none",
                color: "inherit",
                display: "flex",
                alignItems: "center",
              }}
            >
              <Box
                component="img"
                src={`${process.env.PUBLIC_URL}/lawyer-brain-good-logo.png`}
                alt="Lawyer Brain Logo"
                sx={{ height: 40, marginRight: 2 }}
              />
              <Typography variant="h6" component="div">
                Lawyer Brain
              </Typography>
            </Link>
            <Box sx={{ flexGrow: 1 }} />
            <Box sx={{ display: "flex", alignItems: "center", marginRight: 2 }}>
              <Link
                to="/about"
                style={{ textDecoration: "none", color: "inherit" }}
              >
                <Typography variant="h6" component="div">
                  About
                </Typography>
              </Link>
            </Box>
            <Box sx={{ display: "flex", alignItems: "center" }}>
              <FormControlLabel
                control={
                  <Switch checked={darkMode} onChange={handleThemeChange} />
                }
                label={
                  darkMode ? (
                    <DarkModeTwoTone sx={{ verticalAlign: "middle" }} />
                  ) : (
                    <LightModeTwoTone sx={{ verticalAlign: "middle" }} />
                  )
                }
                sx={{ marginRight: 0 }}
              />
            </Box>
          </Toolbar>
        </AppBar>
        <Container
          sx={{
            display: "flex",
            flexDirection: "column",
            flex: 1,
            minWidth: "25%",
          }}
        >
          <Routes>
            <Route path="/" element={<Chatbot />} />
            <Route path="/about" element={<About />} />
          </Routes>
        </Container>
      </Router>
    </ThemeProvider>
  );
};

export default App;
