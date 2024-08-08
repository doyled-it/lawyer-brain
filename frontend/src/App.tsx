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
import Chatbot from "./components/Chatbot";
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
      <AppBar position="sticky">
        <Toolbar>
          <Box
            component="img"
            src={`${process.env.PUBLIC_URL}/lawyer-brain-good-logo.png`}
            alt="Lawyer Brain Logo"
            sx={{ height: 40, marginRight: 2 }}
          />
          <Typography variant="h6" component="div" sx={{ flexGrow: 1 }}>
            Lawyer Brain
          </Typography>
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
      <Container sx={{ display: "flex", flexDirection: "column", flex: 1 }}>
        <Chatbot />
      </Container>
    </ThemeProvider>
  );
};

export default App;
