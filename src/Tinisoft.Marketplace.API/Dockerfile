FROM mcr.microsoft.com/dotnet/aspnet:8.0 AS base
WORKDIR /app
EXPOSE 5005

FROM mcr.microsoft.com/dotnet/sdk:8.0 AS build
WORKDIR /src

COPY ["src/Tinisoft.Marketplace.API/Tinisoft.Marketplace.API.csproj", "src/Tinisoft.Marketplace.API/"]
COPY ["src/Tinisoft.Application/Tinisoft.Application.csproj", "src/Tinisoft.Application/"]
COPY ["src/Tinisoft.Domain/Tinisoft.Domain.csproj", "src/Tinisoft.Domain/"]
COPY ["src/Tinisoft.Infrastructure/Tinisoft.Infrastructure.csproj", "src/Tinisoft.Infrastructure/"]
COPY ["src/Tinisoft.Shared/Tinisoft.Shared.csproj", "src/Tinisoft.Shared/"]

RUN dotnet restore "src/Tinisoft.Marketplace.API/Tinisoft.Marketplace.API.csproj"
COPY . .
WORKDIR "/src/src/Tinisoft.Marketplace.API"
RUN dotnet build "Tinisoft.Marketplace.API.csproj" -c Release -o /app/build

FROM build AS publish
RUN dotnet publish "Tinisoft.Marketplace.API.csproj" -c Release -o /app/publish /p:UseAppHost=false

FROM base AS final
WORKDIR /app
COPY --from=publish /app/publish .
ENTRYPOINT ["dotnet", "Tinisoft.Marketplace.API.dll"]

